from Backend.Apps.AtgDocs.services import KnowledgeDocumentService


def publish_document(context, document_id):
    return KnowledgeDocumentService.publish(context, document_id)


def upload_document_to_drive(context, document_id, folder_name="ATG Docs", make_public=False):
    return KnowledgeDocumentService.upload_to_drive(context, document_id, folder_name=folder_name, make_public=make_public)
