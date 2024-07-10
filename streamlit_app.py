import streamlit as st
from PIL import Image
import os
import io
import cv2
import numpy as np
from facenet_pytorch import MTCNN
import time
import zipfile

mtcnn = MTCNN(keep_all=True, device="cpu")


def detect_faces(image):
    img_array = np.array(image)
    boxes, _ = mtcnn.detect(img_array)
    return boxes


def highlight_faces(image, faces, margin=0.2):
    img_array = np.array(image)
    img_height, img_width, _ = img_array.shape

    for face in faces:
        x1, y1, x2, y2 = face
        top_margin = int((y2 - y1) * margin)
        expanded_top = max(int(y1) - top_margin, 0)

        cv2.rectangle(
            img_array,
            (int(x1), expanded_top),
            (int(x2), int(y2)),
            (255, 0, 0),
            2,
        )
    return Image.fromarray(img_array)


def process_image(image, output_sizes):
    results = {}
    for size, (width, height, max_size_kb) in output_sizes.items():
        img_copy = image.copy()

        # Skalowanie obrazu do szerokości 1200 pikseli
        img_copy = img_copy.resize(
            (1200, int(1200 * img_copy.height / img_copy.width)), Image.LANCZOS
        )

        # Przycinanie obrazu do odpowiednich proporcji
        img_width, img_height = img_copy.size
        aspect_ratio = width / height

        if img_width / img_height > aspect_ratio:
            new_width = int(img_height * aspect_ratio)
            offset = (img_width - new_width) // 2
            img_copy = img_copy.crop((offset, 0, offset + new_width, img_height))
        else:
            new_height = int(img_width / aspect_ratio)
            offset = (img_height - new_height) // 2
            img_copy = img_copy.crop((0, offset, img_width, offset + new_height))

        # Skalowanie obrazu do docelowego rozmiaru
        img_copy = img_copy.resize((width, height), Image.LANCZOS)

        # Kompresja obrazu do spełnienia wymagań dotyczących rozmiaru pliku
        webp_image = io.BytesIO()
        quality = 100
        img_copy.save(webp_image, format="WEBP", quality=quality)
        while webp_image.tell() > max_size_kb * 1024 and quality > 0:
            quality -= 5
            webp_image = io.BytesIO()
            img_copy.save(webp_image, format="WEBP", quality=quality)
        results[size] = webp_image.getvalue()

    return results


def main():
    st.title("Konwerter obrazów do WebP")
    st.write(
        "Witamy w narzędziu do konwersji obrazów na format WebP. Możesz przetwarzać zdjęcia masowo lub pojedynczo. Wybierz odpowiednią opcję z menu po lewej stronie."
    )

    output_sizes = {
        "Miniaturka": (600, 400, 50),  # (width, height, max_size_kb)
        "Banner": (1200, 500, 100),  # (width, height, max_size_kb)
        "Zdjęcie": (1200, 600, 100),  # (width, height, max_size_kb)
    }

    menu = ["Masowe przetwarzanie", "Pojedyncze zdjęcie", "Zdjęcia z Midjourney"]
    choice = st.sidebar.selectbox("Wybierz tryb", menu)

    if choice == "Masowe przetwarzanie":
        st.header("Masowe przetwarzanie zdjęć")
        st.write(
            "Wybierz pliki, które chcesz przetworzyć. Możesz przesłać wiele plików jednocześnie."
        )
        uploaded_files = st.file_uploader(
            "Wybierz pliki", type=["jpg", "png"], accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("Przetwórz zdjęcia") or st.session_state.get(
                "bulk_processing", False
            ):
                st.session_state.bulk_processing = True
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0
                all_files_zip = io.BytesIO()

                with zipfile.ZipFile(all_files_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, uploaded_file in enumerate(uploaded_files):
                        try:
                            image = Image.open(uploaded_file)
                            faces = detect_faces(image)
                            highlighted_image = highlight_faces(image, faces)
                            results = process_image(highlighted_image, output_sizes)

                            st.write(f"Przetworzono: {uploaded_file.name}")
                            for size, img_bytes in results.items():
                                st.download_button(
                                    label=f"Pobierz {size}",
                                    data=img_bytes,
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    mime="image/webp",
                                )
                                if size == "Banner":
                                    zf.writestr(
                                        f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                        img_bytes,
                                    )
                            st.write("---")
                            processed_count += 1
                        except Exception as e:
                            st.error(
                                f"Błąd podczas przetwarzania {uploaded_file.name}: {str(e)}"
                            )

                        progress_bar.progress((i + 1) / len(uploaded_files))

                    end_time = time.time()
                    processing_time = end_time - start_time
                    st.success(
                        f"Przetworzono {processed_count} z {len(uploaded_files)} plików w {processing_time:.2f} sekund."
                    )
                    st.session_state.bulk_processing = False

                    if processed_count > 0:
                        all_files_zip.seek(0)
                        st.download_button(
                            label="Pobierz wszystkie zdjęcia (1200x500)",
                            data=all_files_zip.getvalue(),
                            file_name="processed_images.zip",
                            mime="application/zip",
                        )

    elif choice == "Pojedyncze zdjęcie":
        st.header("Przetwarzanie pojedynczego zdjęcia")
        st.write("Wybierz jedno zdjęcie, które chcesz przetworzyć.")
        uploaded_file = st.file_uploader("Wybierz plik", type=["jpg", "png"])

        if uploaded_file:
            image = Image.open(uploaded_file)
            faces = detect_faces(image)
            st.image(
                highlight_faces(image, faces),
                caption="Oryginalne zdjęcie z zaznaczonymi twarzami",
                use_column_width=True,
            )

            if st.button("Przetwórz"):
                results = process_image(image, output_sizes)

                cols = st.columns(3)
                for i, (size, img_bytes) in enumerate(results.items()):
                    with cols[i % 3]:
                        st.write(f"{size}:")
                        st.image(
                            img_bytes,
                            caption=f"Przetworzone {size}",
                            use_column_width=True,
                        )
                        st.download_button(
                            label=f"Pobierz {size}",
                            data=img_bytes,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                            mime="image/webp",
                        )

    elif choice == "Zdjęcia z Midjourney":
        st.header("Przetwarzanie zdjęć z Midjourney")
        st.write("Wybierz pliki PNG z Midjourney, które chcesz przetworzyć.")
        uploaded_files = st.file_uploader(
            "Wybierz pliki PNG z Midjourney", type=["png"], accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("Przetwórz zdjęcia") or st.session_state.get(
                "midjourney_processing", False
            ):
                st.session_state.midjourney_processing = True
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0
                all_files_zip = io.BytesIO()

                with zipfile.ZipFile(all_files_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, uploaded_file in enumerate(uploaded_files):
                        try:
                            image = Image.open(uploaded_file)
                            faces = detect_faces(image)
                            highlighted_image = highlight_faces(image, faces)
                            results = process_image(highlighted_image, output_sizes)

                            st.write(f"Przetworzono: {uploaded_file.name}")
                            for size, img_bytes in results.items():
                                st.download_button(
                                    label=f"Pobierz {size}",
                                    data=img_bytes,
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    mime="image/webp",
                                )
                                if size == "Banner":
                                    zf.writestr(
                                        f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                        img_bytes,
                                    )
                            st.write("---")
                            processed_count += 1
                        except Exception as e:
                            st.error(
                                f"Błąd podczas przetwarzania {uploaded_file.name}: {str(e)}"
                            )

                        progress_bar.progress((i + 1) / len(uploaded_files))

                    end_time = time.time()
                    processing_time = end_time - start_time
                    st.success(
                        f"Przetworzono {processed_count} z {len(uploaded_files)} plików w {processing_time:.2f} sekund."
                    )
                    st.session_state.midjourney_processing = False

                    if processed_count > 0:
                        all_files_zip.seek(0)
                        st.download_button(
                            label="Pobierz wszystkie zdjęcia (1200x500)",
                            data=all_files_zip.getvalue(),
                            file_name="processed_images.zip",
                            mime="application/zip",
                        )


if __name__ == "__main__":
    main()
