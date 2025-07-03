import copy
from multiprocessing import Pool, cpu_count
from debug_log import print_log
from session import get_session_images_path, new_uuid, copy_file, ensure_path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, UnidentifiedImageError

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

def export_image(image_info):
    src = image_info.get('path')
    dst = image_info.get('external_output_path')
    status, error = copy_file(src, dst)
    image_info['status'] = status
    image_info['error'] = error
    return image_info

def export_images(images_info, output_directory_path):
    success_images_info = []
    error_images_info = []
    output_directory_path = ensure_path(output_directory_path)
    for image_info in images_info:
        name = image_info.get('external_source_path').name
        image_info['external_output_path'] = output_directory_path / name

    with ThreadPoolExecutor() as executor:
        copy_results = list(executor.map(export_image, images_info))
        for image_info in copy_results:
            if image_info.get('status'):
                success_images_info.append(image_info)
            else:
                error_images_info.append(image_info)

    return success_images_info, error_images_info

def save_new_image(image_info, new_img):
    images_folder_path = get_session_images_path(image_info.get('session_id'))
    new_image_info = copy.deepcopy(image_info)
    new_image_info['image_id'] = new_uuid()
    new_image_info['old_image_id'] = image_info.get('image_id')
    new_image_info['path'] = images_folder_path / f'{new_image_info.get('image_id')}--{new_image_info.get('external_source_path').name}'
    new_img.save(new_image_info.get('path'))
    new_image_info['status'] = True
    old_image_info = image_info

    return new_image_info, old_image_info

def resize_image(config):
    try:
        image_info = config.get('image_info')
        width = config.get('width')
        height = config.get('height')
        dpi = config.get('dpi')
        scale = config.get('scale')

        with Image.open(image_info.get('path')) as img:
            
            original_width, original_height = img.size

            match scale:
                case 'px':
                    pts_divider = 72
                case 'mm':
                    pts_divider = 25.4
                case 'cm':
                    pts_divider = 2.54
                case 'm':
                    pts_divider = 0.254
                case 'in':
                    pts_divider = 1
                case 'percentage':
                    pts_divider = 72
                    width = original_width * (width / 100)
                    height = original_height * (height / 100)
                case _:
                    pts_divider = 25.4

            width_px = width * dpi / pts_divider
            height_px = height * dpi / pts_divider

            if width_px > original_width and height_px > original_height:
                algorithm = Image.BICUBIC
            else:
                algorithm = Image.LANCZOS

            resized = img.resize((int(width_px), int(height_px)), algorithm)
            return save_new_image(image_info, resized)
        
    except FileNotFoundError:
        error = f"Arquivo não encontrado: {image_info.get('path')}"
    except UnidentifiedImageError:
        error = f"Arquivo não é uma imagem válida: {image_info.get('path')}"
    except OSError as e:
        error = f"Falha ao processar imagem '{image_info.get('path')}': {e}"
    except ValueError as e:
        error = f"Valor inválido ao salvar '{image_info.get('path')}': {e}"
    except KeyError as e:
        error = f"Formato não suportado para '{image_info.get('path')}': {e}"
    except OSError as e:
        error = f"Falha no sistema de arquivos ao salvar '{image_info.get('path')}': {e}"
    except Exception as e:
        error = f"Erro inesperado com '{image_info.get('path')}': {e}"
    
    image_info['status'] = False
    image_info['error'] = error

    return image_info, []

def resize_images(images_info, width = None, height = None, dpi = 300, scale = 'mm'):
    old_images_info = []
    new_images_info = []
    error_images_info = []
    configs = []

    for image_info in images_info:
        config = {
            'image_info': image_info,
            'width': width,
            'height': height,
            'dpi': dpi,
            'scale': scale
        }
        configs.append(config)

    with Pool(processes=cpu_count()) as pool:
        resize_results = pool.map(resize_image, configs)

    for new_image_info, old_image_info in resize_results:
        if new_image_info.get('status'):
            new_images_info.append(new_image_info)
            if isinstance(old_image_info, dict):
                old_images_info.append(old_image_info)
        else:
            error_images_info.append(new_image_info)

    return new_images_info, old_images_info, error_images_info

def convert_to_px(value, scale, dpi = 300, total_size = None):
    try:
        match(scale):
            case 'px':
                return int(value)
            case 'mm':
                return int(value * dpi / 25.4)
            case 'cm':
                return int(value * dpi / 2.54)
            case 'in':
                return int(value * dpi)
            case 'percentage':
                return int(total_size * value / 100)
            case _:
                raise ValueError(f'Escala não suportada: {scale}')
    except Exception as e:
        raise ValueError(f'Erro ao converter escala "{scale}": {e}')

def edit_border_image(config):
    image_info = config.get('image_info')
    left = config.get('left')
    right = config.get('right')
    top = config.get('top')
    bottom = config.get('bottom')
    scale = config.get('scale')
    type = config.get('type')
    color = config.get('color')
    dpi = config.get('dpi')

    try:
        with Image.open(image_info.get('path')) as img:
            original_width, original_height = img.size

            left_px = convert_to_px(left, scale, dpi, original_width)
            right_px = convert_to_px(right, scale, dpi, original_width)
            top_px = convert_to_px(top, scale, dpi, original_height)
            bottom_px = convert_to_px(bottom, scale, dpi, original_height)

            crop_box = (
                left_px,
                top_px,
                original_width - right_px,
                original_height - bottom_px
            )

            cropped_img = img.crop(crop_box)
            return save_new_image(image_info, cropped_img)

    except FileNotFoundError:
        error = f"Arquivo não encontrado: {image_info.get('path')}"
    except UnidentifiedImageError:
        error = f"Arquivo não é uma imagem válida: {image_info.get('path')}"
    except OSError as e:
        error = f"Falha ao processar imagem '{image_info.get('path')}': {e}"
    except ValueError as e:
        error = f"Valor inválido ao salvar '{image_info.get('path')}': {e}"
    except KeyError as e:
        error = f"Formato não suportado para '{image_info.get('path')}': {e}"
    except OSError as e:
        error = f"Falha no sistema de arquivos ao salvar '{image_info.get('path')}': {e}"
    except Exception as e:
        error = f"Erro inesperado com '{image_info.get('path')}': {e}"

    image_info['status'] = False
    image_info['error'] = error

    return image_info, []
    
def edit_border_images(images_info, left, right, top, bottom, scale, type, color, dpi):
    old_images_info = []
    new_images_info = []
    error_images_info = []
    configs = []

    for image_info in images_info:
        config = {
            'image_info': image_info,
            'left': left,
            'right': right,
            'top': top,
            'bottom': bottom,
            'scale': scale,
            'type': type,
            'color': color,
            'dpi': dpi
        }
        configs.append(config)

    with Pool(processes=cpu_count()) as pool:
        cropped_results = pool.map(edit_border_image, configs)

    for new_image_info, old_image_info in cropped_results:
        if new_image_info.get('status'):
            new_images_info.append(new_image_info)
            if isinstance(old_image_info, dict):
                old_images_info.append(old_image_info)
        else:
            error_images_info.append(new_image_info)

    return new_images_info, old_images_info, error_images_info










    













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