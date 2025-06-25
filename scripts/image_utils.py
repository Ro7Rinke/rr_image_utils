from session import get_session_images_path, new_uuid, copy_file, ensure_path
from concurrent.futures import ThreadPoolExecutor

def import_image(image_info):
    src = image_info.get('external_source_path')
    dst = image_info.get('path')
    status, error = copy_file(src, dst)
    image_info['status'] = status
    image_info['error'] = error
    return image_info


def import_images(session_id, images_path):
    images_folder_path = get_session_images_path(session_id)
    import_images_info = []
    images_info = []
    error_images_info = []
    for image_path in images_path:
        image_path = ensure_path(image_path)
        image_id = new_uuid()
        image_info = {
            'external_source_path': image_path,
            'id': image_id,
            'session_id': session_id,
            'path': images_folder_path / f'{image_id}--{image_path.name}'
        }
        import_images_info.append(image_info)
    
    with ThreadPoolExecutor() as executor:
        copy_results = list(executor.map(import_image, import_images_info))
        for result_image_info in copy_results:
            if result_image_info.get('status'):
                images_info.append(result_image_info)
            else:
                error_images_info.append(result_image_info)

    return images_info, error_images_info















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