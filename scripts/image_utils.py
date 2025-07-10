import copy
import subprocess
import fitz
from multiprocessing import Pool, cpu_count
from debug_log import print_log
from session import get_session_images_path, new_uuid, copy_file, ensure_path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, UnidentifiedImageError
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import io

def import_image(image_info):
    src = image_info.get('external_source_path')
    dst = image_info.get('path')
    status, error = copy_file(src, dst)
    image_info['status'] = status
    image_info['error'] = error
    return image_info

def get_images_path_from_dirs(dir_images_path):
    new_images_path = []
    for image_path in dir_images_path:
        image_path = ensure_path(image_path)
        if image_path.is_dir():
            all_files = [p for p in image_path.iterdir() if p.is_file() and not p.name.startswith('.')]
            new_images_path.extend(all_files)
        else:
            new_images_path.append(image_path)
    
    return new_images_path

def import_images(session_id, images_path):
    images_folder_path = get_session_images_path(session_id)
    import_images_info = []
    images_info = []
    error_images_info = []

    images_path = get_images_path_from_dirs(images_path)

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

def import_images_from_pdf(session_id, pdfs_path, page_as_image = True, dpi = 300):
    images_folder_path = get_session_images_path(session_id)
    images_info = []

    for pdf_path in pdfs_path:
        pdf_path = ensure_path(pdf_path)
        pdf_doc = fitz.open(pdf_path)

        for page_index in range(len(pdf_doc)):
            page = pdf_doc[page_index]
            page_number = page_index + 1

            if page_as_image:
                pix = page.get_pixmap(dpi=dpi)
                image_id = new_uuid()
                image_info = {
                    'external_source_path': images_folder_path / f'{pdf_path.stem}_{page_number}.png',
                    'id': image_id,
                    'session_id': session_id,
                    'path': images_folder_path / f'{image_id}--{pdf_path.stem}_{page_number}.png'
                }
                pix.save(image_info.get('path'))
                images_info.append(image_info)
            else:
                images = page.get_images(full=True)

                for image_index, image in enumerate(images):
                    xref = image[0]
                    base_image = pdf_doc.extract_image(xref)
                    image_bytes = base_image['image']
                    image_ext = base_image['ext']
                    image_id = new_uuid()
                    image_info = {
                        'external_source_path': images_folder_path / f'{pdf_path.stem}_{page_number}.{image_ext}',
                        'id': image_id,
                        'session_id': session_id,
                        'path': images_folder_path / f'{image_id}--{pdf_path.stem}_{page_number}.{image_ext}'
                    }
                    with open(image_info.get('path'), 'wb') as file:
                        file.write(image_bytes)
                    
                    images_info.append(image_info)

    return images_info, []
    

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
    old_image_info = None
    images_folder_path = get_session_images_path(image_info.get('session_id'))
    new_image_info = copy.deepcopy(image_info)
    new_image_info['image_id'] = new_uuid()
    if image_info.get('image_id') is not None:
        new_image_info['old_image_id'] = image_info.get('image_id')
        old_image_info = image_info
    new_image_info['path'] = images_folder_path / f'{new_image_info.get('image_id')}--{new_image_info.get('external_source_path').name}'
    new_img.save(new_image_info.get('path'))
    new_image_info['status'] = True

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

def export_to_word(images_info, output_directory_path, dpi = None, file_name = None):
    success_images_info = []
    error_images_info = []

    doc = Document()

    section = doc.sections[0]
    section.page_height = Inches(11.69)
    section.page_width = Inches(8.27)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.right_margin = Inches(1)
    section.left_margin = Inches(1)

    for image_info in images_info:
        error = None
        try:
            with Image.open(image_info.get('path')) as img:
                width_px, height_px = img.size
                image_dpi = dpi or img.info.get('dpi', (72, 72))[0]

                width_in = width_px / image_dpi
                height_in = height_px / image_dpi

                paragraph = doc.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

                run = paragraph.add_run()
                run.add_picture(str(image_info.get('path')), width=Inches(width_in), height=Inches(height_in))

                doc.add_page_break()

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
        except Exception as e:
            error = f"Erro inesperado com '{image_info.get('path')}': {e}"
        
        if error:
            image_info['error'] = error
            image_info['status'] = False
            error_images_info.append(image_info)
        else:
            image_info['status'] = True
            success_images_info.append(image_info)

    if doc.paragraphs[-1].text == '':
        doc.paragraphs[-1]._element.getparent().remove(doc.paragraphs[-1]._element)

    output_directory_path = ensure_path(output_directory_path)
    file_name = f'doc_of_images.docx' if file_name is None else f'{file_name}.docx'
    output_path =  output_directory_path / file_name
    doc.save(output_path)

    return success_images_info, error_images_info

def rotate_if_needed(img, max_width, max_height):
    img_width, img_height = img.size
    if img_width > max_width or img_height > max_height:
        if img_height <= max_width and img_width <= max_height:
            return img.rotate(90, expand=True)
    return img

def get_buffer_image(config):
    image_info = config.get('image_info')
    dpi = config.get('dpi')
    page_width = config.get('page_width')
    page_height = config.get('page_height')

    try:
        with Image.open(image_info.get('path')) as img:
            img = rotate_if_needed(img, page_width, page_height)
            img_width, img_height = img.size
            
            image_dpi = dpi or img.info.get('dpi', (72, 72))[0]
            img_width_pts = img_width * (72 / image_dpi)
            img_height_pts = img_height * (72 / image_dpi)
            
            x = (page_width - img_width_pts) / 2
            y = (page_height - img_height_pts) / 2
            
            img_format = img.format or 'PNG'
            buffer = io.BytesIO()
            img.save(buffer, format=img_format)
            buffer.seek(0)

            image_info['error'] = None
            image_info['status'] = True

            result = {
                'buffer': buffer,
                'x': x,
                'y': y,
                'img_width_pts': img_width_pts, 
                'img_height_pts': img_height_pts
            }

            return image_info, result

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
    except Exception as e:
        error = f"Erro inesperado com '{image_info.get('path')}': {e}"

    image_info['error'] = error
    image_info['status'] = False

    return image_info, None

def export_to_pdf(images_info, output_directory_path, dpi=None, file_name = None):
    success_images_info = []
    error_images_info = []
    configs = []
    
    file_name = f'pdf_of_images.pdf' if file_name is None else f'{file_name}.pdf'
    output_directory_path = ensure_path(output_directory_path)
    output_pdf_path =  output_directory_path / file_name

    page_width, page_height = A4
    
    c = canvas.Canvas(str(output_pdf_path), pagesize=A4)

    for image_info in images_info:
        config = {
            'image_info': image_info,
            'dpi': dpi,
            'page_width': page_width,
            'page_height': page_height
        }
        configs.append(config)

    with Pool(processes=cpu_count()) as pool:
        buffer_results = pool.map(get_buffer_image, configs)

    for image_info, result in buffer_results:
        if image_info.get('status'):
            buffer = result.get('buffer')
            x = result.get('x')
            y = result.get('y')
            img_width_pts = result.get('img_width_pts')
            img_height_pts = result.get('img_height_pts')

            c.drawImage(
                ImageReader(buffer),
                x, y,
                width=img_width_pts,
                height=img_height_pts,
                mask='auto',
                preserveAspectRatio=True,
            )
            c.showPage()
            success_images_info.append(image_info)
        else:
            error_images_info.append(image_info)

    c.save()

    return success_images_info, error_images_info

def get_from_grid(config):
    image_info = config.get('image_info')
    rows = config.get('rows')
    cols = config.get('cols')
    new_images_info = []

    # try:
    with Image.open(image_info.get('path')) as img:
        img_width, img_height = img.size
        cell_width = img_width // cols
        cell_height = img_height // rows

        for row in range(rows):
            for col in range(cols):
                left = col * cell_width
                upper = row * cell_height
                right = left + cell_width
                lower = upper + cell_height

                box = (left, upper, right, lower)
                cropped = img.crop(box)

                original_name = image_info.get('path').stem
                new_image_info = {
                    'external_source_path': ensure_path(f"{original_name}_{row}_{col}.png"),
                    'session_id': image_info.get('session_id')
                }
                new_image_info = save_new_image(new_image_info, cropped)
                new_images_info.append(new_image_info)
        
        return new_images_info

    # except FileNotFoundError:
    #         error = f"Arquivo não encontrado: {image_info.get('path')}"
    # except UnidentifiedImageError:
    #     error = f"Arquivo não é uma imagem válida: {image_info.get('path')}"
    # except OSError as e:
    #     error = f"Falha ao processar imagem '{image_info.get('path')}': {e}"
    # except ValueError as e:
    #     error = f"Valor inválido ao salvar '{image_info.get('path')}': {e}"
    # except KeyError as e:
    #     error = f"Formato não suportado para '{image_info.get('path')}': {e}"
    # except Exception as e:
    #     error = f"Erro inesperado com '{image_info.get('path')}': {e}"

def images_from_grid(images_info, rows = 1, cols = 1):
    new_images_info = []
    configs = []

    for image_info in images_info:
        config = {
            'image_info': image_info,
            'cols': cols,
            'rows': rows
        }
        configs.append(config)

    with Pool(processes=cpu_count()) as pool:
        cropped_results = pool.map(get_from_grid, configs)
        new_images_info.extend(cropped_results)

    return new_images_info

def quicklook_images(images_info):
    paths = []
    
    for image_info in images_info:
        image_path = ensure_path(image_info.get('path'))
        if image_path.is_file():
            paths.append(str(image_path))

    subprocess.run(["qlmanage", "-p"] + paths)

# --action from_grid --rows 3 --cols 3

# /Users/ro7rinke/Library/CloudStorage/GoogleDrive-ro7rinke2@gmail.com/My Drive/BoardGame/Brass Birmingham/final-print/cards/cards_grid_1.jpg

# --output_directory_path "/Users/ro7rinke/Documents/rr_image_utils/data/temp"

# --action to_pdf --file_name brass --output_directory_path "/Users/ro7rinke/Documents/rr_image_utils/data/temp"
    













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