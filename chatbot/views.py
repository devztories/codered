import os, requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .models import ChatConversation, ChatMessage

SYSTEM_PROMPT = """You are the professional project consultant and front-desk administrator of CODERED INVENTIONS. Respond ONLY in clear, natural English. Never use Malayalam, Manglish, transliteration, or mixed-language replies, even if the visitor writes in another language.

Act like a thoughtful human project coordinator. Understand the visitor's goal, ask one useful question at a time, and remember details already provided. Never repeat the same question or send the same reply twice in a conversation. If a detail is already known, move to the next missing detail.

We handle Business Projects and Academic Projects. Academic projects can be Ready-made (direct purchase or optional extra-feature customization) or Build Your Own. Build Your Own academic projects can be Single Person or Group projects. For group projects, collect the group size and each member's full name, one at a time if needed.

For custom projects, clarify project name/idea, requested features, technologies, budget, deadline and relevant requirements. Ask conversationally, not as a long form. For ready-made projects, only mention catalogue products and prices that are actually supplied by the website; ask whether the visitor wants to buy as-is or add specific features. Never invent catalogue items, prices, delivery dates, or payment confirmation.

UPI QR payments are verified by staff after proof is submitted. Never claim payment is complete until the system confirms it. Certificates are generated only after verified payment and project completion. For complex requests or human support, direct the visitor to Contact or Start Your Project. Be concise, helpful, and avoid repeating details already shared."""

def fallback_reply(history, text):
    t = text.lower()
    if any(x in t for x in ["contact us", "contact", "phone number", "call you", "whatsapp", "human support"]):
        try:
            from contact.models import SiteSettings
            info = SiteSettings.objects.first()
            phone = info.phone if info else ""
            whatsapp = info.whatsapp_number if info else ""
            parts = ["You can reach the CODERED INVENTIONS team here:"]
            if phone:
                parts.append(f"Phone: {phone}")
            if whatsapp:
                parts.append(f"WhatsApp: {whatsapp}")
            if info and info.contact_email:
                parts.append(f"Email: {info.contact_email}")
            if len(parts) == 1:
                parts.append("Please use the Contact page and our team will get back to you.")
            return "\\n".join(parts)
        except Exception:
            return "Please use the Contact page to reach our team. We will be happy to help."

    previous = next((content for sender, content in reversed(history[:-1]) if sender in {"ai", "admin"}), "")
    if any(x in t for x in ["hello", "hi", "hey"]):
        answer = "Hello! Welcome to CODERED INVENTIONS. What would you like to create or purchase today?"
    elif any(x in t for x in ["academic", "college", "final year", "student"]):
        answer = "For an academic project, would you prefer a ready-made project or a new project built around your own idea?"
    elif any(x in t for x in ["ready made", "readymade", "buy", "purchase", "ready-made"]):
        answer = "Would you like to purchase the ready-made project as it is, or add a few custom features before delivery?"
    elif any(x in t for x in ["group", "team", "members"]):
        answer = "Is this a group project? If yes, how many students should receive individual certificates?"
    elif any(x in t for x in ["business", "company", "website", "software", "automation"]):
        answer = "What should the solution help your business do: manage operations, reach customers, automate a task, or something else?"
    elif any(x in t for x in ["budget", "price", "cost", "rate"]):
        answer = "What budget range have you planned for this project? I can use that to guide the scope."
    elif any(x in t for x in ["deadline", "date", "when"]):
        answer = "What is your target completion date? An approximate date is fine if it is not fixed yet."
    elif any(x in t for x in ["feature", "add", "module"]):
        answer = "Which specific feature would make the biggest difference to your project?"
    elif any(x in t for x in ["start", "build", "develop", "create", "project"]):
        answer = "What name or short idea would you like to give the project?"
    else:
        answer = "I can help with a business solution, an academic project, or customization of a ready-made project. Which one are you considering?"
    if answer.strip().casefold() == previous.strip().casefold():
        answer = "Thanks, I have that detail. What is the next important requirement you would like us to consider?"
    return answer

@require_POST
@csrf_protect
def message(request):
    text=request.POST.get('message','').strip()
    if not text or len(text)>2000:
        return JsonResponse({'error':'Enter a message under 2,000 characters.'},status=400)
    if not request.session.session_key: request.session.create()
    conv=ChatConversation.objects.filter(user=request.user if request.user.is_authenticated else None,session_key=request.session.session_key).first()
    if not conv: conv=ChatConversation.objects.create(user=request.user if request.user.is_authenticated else None,session_key=request.session.session_key)
    ChatMessage.objects.create(conversation=conv,sender='user',content=text)
    if conv.mode=='human':
        answer='Your conversation has been forwarded to our support team. Please share any remaining project details and a team member will follow up.'
        sender='admin'
    else:
        key=os.getenv('AI_API_KEY'); url=os.getenv('AI_API_URL','https://api.openai.com/v1/chat/completions'); model=os.getenv('AI_MODEL','gpt-4o-mini')
        answer=''
        if key:
            try:
                history=[{'role':'system','content':SYSTEM_PROMPT}]
                history += [{'role':'user' if m.sender=='user' else 'assistant','content':m.content} for m in conv.messages.order_by('-created_at', '-id')[:14][::-1]]
                r=requests.post(url,headers={'Authorization':f'Bearer {key}'},json={'model':model,'messages':history,'temperature':0.65},timeout=25)
                r.raise_for_status(); answer=r.json()['choices'][0]['message']['content'].strip()
            except Exception:
                answer='I am unable to connect to the assistant right now. Please submit your project idea through the Start Your Project form, and our team will follow up.'
        else:
            history=list(conv.messages.order_by('created_at', 'id').values_list('sender','content'))
            answer=fallback_reply(history,text)
        sender='ai'
    previous_ai = conv.messages.filter(sender__in=['ai', 'admin']).order_by('-created_at').first()
    if previous_ai and previous_ai.content.strip().casefold() == answer.strip().casefold():
        answer = 'I have noted that. Could you share the next detail so I can guide you further?'
    ChatMessage.objects.create(conversation=conv,sender=sender,content=answer)
    return JsonResponse({'reply':answer})
