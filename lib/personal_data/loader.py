"""Load personal data like LinkedIn profile and summary."""

from pypdf import PdfReader
from typing import NamedTuple


class PersonalData(NamedTuple):
    """Container for personal data."""
    name: str
    summary: str
    linkedin: str


def load_personal_data(name: str = "Seung-Gu") -> PersonalData:
    """Load personal data from files.
    
    Args:
        name: Name of the person
    
    Returns:
        PersonalData with name, summary, and linkedin content
    """
    # Load LinkedIn profile
    reader = PdfReader("me/linkedin.pdf")
    linkedin = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            linkedin += text
    
    # Load summary
    with open("me/summary.txt", "r", encoding="utf-8") as f:
        summary = f.read()
    
    return PersonalData(name=name, summary=summary, linkedin=linkedin)

