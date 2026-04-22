from fluvius.dform.form import FormModel, FormElement

class ApplicantInfoForm(FormModel):
    """Primary applicant personal details"""
    personal_info: FormElement("personal-info", param={"required": True})

    class Meta:
        key = "applicant-info"
        name = "Applicant Information"
        desc = "Primary applicant personal details"
        header = "Primary Applicant"
        footer = "All information will be verified."