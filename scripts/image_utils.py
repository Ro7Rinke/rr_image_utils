from session import get_session_images_path, new_uuid, copy_file, ensure_path

def import_images(session_id, images_path):
    images_folder_path = get_session_images_path(session_id)
    images_info = []
    for image_path in images_path:
        image_path = ensure_path(image_path)
        image_id = new_uuid()
        image_info = {
            'external_source_path': image_path,
            'id': image_id,
            'session_id': session_id,
            'path': images_folder_path / f'{image_id}--{image_path.name}'
        }
        copy_file(image_path, image_info['path'])
        images_info.append(image_info)

    return images_info















# def test():
#     image_info = {
#         'external_source_path': '', #Path
#         'external_destination_path': '', #Path
#         'path': '', #Path
#         'session_id': '',
#         'id': '',
#         'old_id': '',
#         'original_name': '',
#         'original_extension': '',
#     }
#     return