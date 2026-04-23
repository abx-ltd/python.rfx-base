from fluvius.dform.form import FormModel, FormElement

class ApplicantInfoForm(FormModel):
    """Primary applicant personal details"""

    full_name: FormElement(
        "short-answer",
        param={
            "label": "Full Name",
            "required": True,
            "placeholder": "Enter your full name"
        }
    )

    email: FormElement(
        "short-answer",
        param={
            "label": "Email",
            "required": True
        }
    )

    bio: FormElement(
        "paragraph",
        param={
            "label": "About You"
        }
    )

    position: FormElement(
        "select",
        param={
            "label": "Position",
            "options": ["Backend", "Frontend", "AI Engineer"],
            "required": True
        }
    )

    skills: FormElement(
        "checkbox",
        param={
            "label": "Skills",
            "options": ["Python", "SQL", "Docker"]
        }
    )

    note: FormElement(
        "text-input",
        param={
            "text": "All information will be verified."
        }
    )

    # personal_info: FormElement("personal-info", param={"required": True})
    # address: FormElement("address", param={"required": True, "label": "Current Address"})
    # phone: FormElement("phone-number", param={"required": True})
    # email: FormElement("email", param={"required": True})

    class Meta:
        key = "applicant-info"
        name = "Applicant Information"
        desc = "Primary applicant personal details"
        header = "Primary Applicant"
        footer = "All information will be verified."