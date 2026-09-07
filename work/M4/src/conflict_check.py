"""Détection de conflit entre sources actives, sans règle de priorité vérifiable.

`DOC-RAG-OPS-001` impose : « [le système] s'abstient... lorsque deux
révisions actives se contredisent sans règle de priorité vérifiable ». Ce
module donne un contrôle vérifiable à ce contrat : deux documents admissibles
qui prétendent l'un et l'autre faire autorité sur le même sujet (même
``topic``) sans lien de succession explicite (``supersedes_document_id``)
sont un conflit non résolu.
"""

from __future__ import annotations


def has_unresolved_conflict(documents: list[dict[str, str]]) -> bool:
    """True si au moins deux documents admissibles du même ``topic`` sont
    actifs sans qu'aucun ne remplace explicitement l'autre."""
    by_topic: dict[str, list[dict[str, str]]] = {}
    for document in documents:
        topic = document.get("topic")
        if not topic:
            continue
        by_topic.setdefault(topic, []).append(document)

    for group in by_topic.values():
        active = [doc for doc in group if doc.get("status") == "active"]
        if len(active) < 2:
            continue
        resolved_ids = {doc.get("supersedes_document_id") for doc in active if doc.get("supersedes_document_id")}
        active_ids = {doc["document_id"] for doc in active}
        # Un conflit est résolu seulement si chaque paire active est reliée
        # par une chaîne de succession explicite couvrant tous les documents
        # sauf un (le plus récent).
        if len(active_ids - resolved_ids) > 1:
            return True
    return False
