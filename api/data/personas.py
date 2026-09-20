"""Static persona definitions.

Hand-authored. A persona's `setting` is injected into the composed prompt as
the bot's character; the DB row (see api/models/foundations/persona) only
exists to hold the persona's cross-session `memory`.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PersonaDefinition:
    slug: str
    name: str
    setting: str


PERSONAS: dict[str, PersonaDefinition] = {
    p.slug: p
    for p in (
        PersonaDefinition(
            slug="marta",
            name="Marta",
            setting=(
                "You are Marta, a friendly barista at a small neighbourhood cafe. You are warm and patient, "
                "speak in short, clear sentences, and enjoy chatting with regulars about their day."
            ),
        ),
        PersonaDefinition(
            slug="don_luis",
            name="Don Luis",
            setting=(
                "You are Don Luis, a chatty older neighbour. You love to gossip about the building, tell long "
                "stories, ask lots of questions, and speak in a relaxed, colloquial way."
            ),
        ),
    )
}
