import streamlit as st
from PIL import Image
import os
import io
import time


def process_image(image, output_sizes):
    results = {}
    for size, (width, height, max_size_kb) in output_sizes.items():
        img_copy = image.copy()

        # Resize image to 1200 pixels wide
        img_copy = img_copy.resize(
            (1200, int(1200 * img_copy.height / img_copy.width)), Image.LANCZOS
        )

        # Crop image to correct aspect ratio
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

        # Resize image to target size
        img_copy = img_copy.resize((width, height), Image.LANCZOS)

        # Compress image to meet file size requirements
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

        if uploaded_files and st.button("Przetwórz zdjęcia"):
            st.session_state.bulk_processing = True
            progress_bar = st.progress(0)
            start_time = time.time()
            processed_count = 0

            processed_images = []

            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    image = Image.open(uploaded_file)
                    results = process_image(image, output_sizes)

                    st.write(f"Przetworzono: {uploaded_file.name}")
                    for size, img_bytes in results.items():
                        if size == "Zdjęcie":
                            processed_images.append(
                                (
                                    f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    img_bytes,
                                )
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
                st.markdown("### Pobierz wszystkie zdjęcia (1200x600)")
                for filename, img_bytes in processed_images:
                    st.download_button(
                        label=f"Pobierz {filename}",
                        data=img_bytes,
                        file_name=filename,
                        mime="image/webp",
                    )

    elif choice == "Pojedyncze zdjęcie":
        st.header("Przetwarzanie pojedynczego zdjęcia")
        st.write("Wybierz jedno zdjęcie, które chcesz przetworzyć.")
        uploaded_file = st.file_uploader("Wybierz plik", type=["jpg", "png"])

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(
                image,
                caption="Oryginalne zdjęcie",
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

        if uploaded_files and st.button("Przetwórz zdjęcia"):
            st.session_state.midjourney_processing = True
            progress_bar = st.progress(0)
            start_time = time.time()
            processed_count = 0

            processed_images = []

            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    image = Image.open(uploaded_file)
                    results = process_image(image, output_sizes)

                    st.write(f"Przetworzono: {uploaded_file.name}")
                    for size, img_bytes in results.items():
                        if size == "Zdjęcie":
                            processed_images.append(
                                (
                                    f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    img_bytes,
                                )
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
                st.markdown("### Pobierz wszystkie zdjęcia (1200x600)")
                for filename, img_bytes in processed_images:
                    st.download_button(
                        label=f"Pobierz {filename}",
                        data=img_bytes,
                        file_name=filename,
                        mime="image/webp",
                    )


if __name__ == "__main__":
    main()
