from django import forms
from catalog.models import Project
from .models import ProjectRequest


class ProjectRequestForm(forms.ModelForm):
    class Meta:
        model = ProjectRequest
        fields = (
            "request_type", "academic_team_type", "group_size", "group_member_names", "project", "title", "category", "required_features",
            "customization_features", "technologies", "requirements", "budget", "deadline",
            "reference_file",
        )
        labels = {
            "request_type": "Request type",
            "academic_team_type": "Academic project type",
            "group_size": "Number of group members",
            "group_member_names": "Full names of all group members (one per line)",
            "project": "Selected catalogue project (optional)",
            "title": "Project name",
            "category": "Project category",
            "required_features": "Features you need",
            "customization_features": "Additional features to add",
            "technologies": "Preferred technologies",
            "requirements": "Project description / requirements",
            "budget": "Your budget (INR)",
            "deadline": "Required deadline",
            "reference_file": "Reference file (optional)",
        }
        help_texts = {
            "project": "If you opened this form from a project card, that project is selected automatically.",
            "title": "Enter the name or working title of your project.",
            "required_features": "List the main modules and features you expect.",
            "customization_features": "For a ready-made project, mention only the extra features you want added.",
            "budget": "Enter your expected budget. You can leave it blank if you need a quotation.",
            "deadline": "Choose the date by which you need the project.",
            "reference_file": "Attach a brief, image, PDF or other reference.",
        }
        widgets = {
            "request_type": forms.Select(attrs={"class": "form-select"}),
            "academic_team_type": forms.Select(attrs={"class": "form-select", "id": "id_academic_team_type"}),
            "group_size": forms.NumberInput(attrs={"class": "form-control", "min": "2", "max": "20", "placeholder": "e.g. 4"}),
            "group_member_names": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Student 1 full name\nStudent 2 full name"}),
            "project": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Smart Attendance System"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "required_features": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Login, dashboard, reports..."}),
            "customization_features": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Only list the extra features you want added..."}),
            "technologies": forms.TextInput(attrs={"class": "form-control", "placeholder": "Python, Django, React..."}),
            "requirements": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Explain your idea and any special requirements..."}),
            "budget": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Your approximate budget", "min": "0", "step": "0.01"}),
            "deadline": forms.DateInput(attrs={"class": "form-control date-entry", "type": "date", "inputmode": "numeric", "autocomplete": "off", "placeholder": "YYYY-MM-DD"}),
            "reference_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all().select_related("category").order_by("name")
        for name in ("project", "category", "budget", "deadline", "reference_file", "customization_features", "technologies", "requirements", "required_features", "group_size", "group_member_names"):
            self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        request_type = cleaned.get("request_type")
        selected_project = cleaned.get("project")
        if selected_project:
            # Catalogue details are authoritative whenever a catalogue card was selected.
            cleaned["title"] = selected_project.name
            cleaned["category"] = selected_project.category
        if request_type == "ready_custom":
            if not selected_project:
                self.add_error("project", "Choose the ready-made academic project you want to customize.")
            if not cleaned.get("customization_features"):
                self.add_error("customization_features", "Tell us which additional features you want.")
        else:
            if not cleaned.get("title"):
                self.add_error("title", "Enter your project name.")
            if not cleaned.get("required_features"):
                self.add_error("required_features", "Describe the main features you need.")
        if request_type == "academic_custom":
            team_type = cleaned.get("academic_team_type") or "single"
            if team_type == "group":
                names = [line.strip() for line in (cleaned.get("group_member_names") or "").splitlines() if line.strip()]
                count = cleaned.get("group_size") or 0
                if count < 2:
                    self.add_error("group_size", "A group must contain at least two members.")
                if len(names) != count:
                    self.add_error("group_member_names", f"Enter exactly {count} member names, one per line.")
                elif len({name.casefold() for name in names}) != len(names):
                    self.add_error("group_member_names", "Each group member must have a distinct full name.")
            else:
                cleaned["group_size"] = 1
                cleaned["group_member_names"] = ""
        return cleaned
