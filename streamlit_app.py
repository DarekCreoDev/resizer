import streamlit as st
from PIL import Image
import os
import io
import time
import zipfile


def process_image(image, output_sizes):
    results = {}
    for size, (width, height, max_size_kb) in output_sizes.items():
        img_copy = image.copy()
        img_copy = img_copy.resize(
            (1200, int(1200 * img_copy.height / img_copy.width)), Image.LANCZOS
        )

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

        img_copy = img_copy.resize((width, height), Image.LANCZOS)

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
        "Miniaturka": (600, 400, 50),
        "Banner": (1200, 500, 100),
        "Zdjęcie": (1200, 600, 100),
    }

    menu = [
        "Masowe przetwarzanie 🥑",
        "Pojedyncze zdjęcie 🥑",
        "Zdjęcia z Midjourney 🥑",
        "Niestandardowy rozmiar",
    ]
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
            if st.button("Przetwórz zdjęcia"):
                st.session_state.bulk_processing = True
                st.session_state.processed_images = []

            if st.session_state.get("bulk_processing", False):
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0

                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        results = process_image(image, output_sizes)
                        st.write(f"Przetworzono: {uploaded_file.name}")

                        cols = st.columns(3)
                        for idx, (size, img_bytes) in enumerate(results.items()):
                            with cols[idx]:
                                st.image(
                                    img_bytes, caption=f"{size}", use_column_width=True
                                )
                                st.download_button(
                                    label=f"Pobierz {size}",
                                    data=img_bytes,
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    mime="image/webp",
                                )

                        st.session_state.processed_images.append(
                            (uploaded_file.name, results)
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

            if st.session_state.get("processed_images", []):
                if st.button("Pobierz wszystkie zdjęcia"):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(
                        zip_buffer, "w", zipfile.ZIP_DEFLATED
                    ) as zip_file:
                        for file_name, results in st.session_state.processed_images:
                            img_bytes = results["Zdjęcie"]
                            zip_file.writestr(
                                f"{os.path.splitext(file_name)[0]}_1200x600.webp",
                                img_bytes,
                            )

                    st.download_button(
                        label="Pobierz wszystkie zdjęcia (1200x600)",
                        data=zip_buffer.getvalue(),
                        file_name="wszystkie_zdjecia.zip",
                        mime="application/zip",
                    )

    elif choice == "Pojedyncze zdjęcie":
        st.header("Przetwarzanie pojedynczego zdjęcia")
        st.write("Wybierz jedno zdjęcie, które chcesz przetworzyć.")
        uploaded_file = st.file_uploader("Wybierz plik", type=["jpg", "png"])

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Oryginalne zdjęcie", use_column_width=True)

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
            if st.button("Przetwórz zdjęcia"):
                st.session_state.midjourney_processing = True
                st.session_state.processed_midjourney_images = []

            if st.session_state.get("midjourney_processing", False):
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0

                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        results = process_image(image, output_sizes)
                        st.write(f"Przetworzono: {uploaded_file.name}")

                        cols = st.columns(3)
                        for idx, (size, img_bytes) in enumerate(results.items()):
                            with cols[idx]:
                                st.image(
                                    img_bytes, caption=f"{size}", use_column_width=True
                                )
                                st.download_button(
                                    label=f"Pobierz {size}",
                                    data=img_bytes,
                                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{size}.webp",
                                    mime="image/webp",
                                )

                        st.session_state.processed_midjourney_images.append(
                            (uploaded_file.name, results)
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

            if st.session_state.get("processed_midjourney_images", []):
                if st.button("Pobierz wszystkie zdjęcia"):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(
                        zip_buffer, "w", zipfile.ZIP_DEFLATED
                    ) as zip_file:
                        for (
                            file_name,
                            results,
                        ) in st.session_state.processed_midjourney_images:
                            img_bytes = results["Zdjęcie"]
                            zip_file.writestr(
                                f"{os.path.splitext(file_name)[0]}_1200x600.webp",
                                img_bytes,
                            )

                    st.download_button(
                        label="Pobierz wszystkie zdjęcia (1200x600)",
                        data=zip_buffer.getvalue(),
                        file_name="wszystkie_zdjecia_midjourney.zip",
                        mime="application/zip",
                    )

    elif choice == "Niestandardowy rozmiar":
        st.header("Przetwarzanie zdjęć w niestandardowym rozmiarze")
        st.write(
            "Wybierz pliki i określ niestandardowy rozmiar dla przetwarzanych zdjęć."
        )

        custom_width = st.number_input(
            "Szerokość (px)", min_value=100, max_value=1920, value=1920
        )
        custom_height = st.number_input(
            "Wysokość (px)", min_value=100, max_value=1080, value=1080
        )
        custom_max_size = st.number_input(
            "Maksymalny rozmiar pliku (KB)", min_value=50, max_value=1000, value=100
        )

        custom_output_sizes = {
            "Niestandardowy": (custom_width, custom_height, custom_max_size)
        }

        uploaded_files = st.file_uploader(
            "Wybierz pliki", type=["jpg", "png"], accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("Przetwórz zdjęcia"):
                st.session_state.custom_processing = True
                st.session_state.processed_custom_images = []

            if st.session_state.get("custom_processing", False):
                progress_bar = st.progress(0)
                start_time = time.time()
                processed_count = 0

                for i, uploaded_file in enumerate(uploaded_files):
                    try:
                        image = Image.open(uploaded_file)
                        results = process_image(image, custom_output_sizes)
                        st.write(f"Przetworzono: {uploaded_file.name}")

                        cols = st.columns(2)
                        with cols[0]:
                            st.image(
                                image,
                                caption="Oryginalne zdjęcie",
                                use_column_width=True,
                            )
                        with cols[1]:
                            st.image(
                                results["Niestandardowy"],
                                caption=f"Przetworzone {custom_width}x{custom_height}",
                                use_column_width=True,
                            )
                            st.download_button(
                                label=f"Pobierz {custom_width}x{custom_height}",
                                data=results["Niestandardowy"],
                                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_{custom_width}x{custom_height}.webp",
                                mime="image/webp",
                            )

                        st.session_state.processed_custom_images.append(
                            (uploaded_file.name, results)
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

            if st.session_state.get("processed_custom_images", []):
                if st.button("Pobierz wszystkie zdjęcia"):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(
                        zip_buffer, "w", zipfile.ZIP_DEFLATED
                    ) as zip_file:
                        for (
                            file_name,
                            results,
                        ) in st.session_state.processed_custom_images:
                            img_bytes = results["Niestandardowy"]
                            zip_file.writestr(
                                f"{os.path.splitext(file_name)[0]}_{custom_width}x{custom_height}.webp",
                                img_bytes,
                            )

                    st.download_button(
                        label=f"Pobierz wszystkie zdjęcia ({custom_width}x{custom_height})",
                        data=zip_buffer.getvalue(),
                        file_name=f"wszystkie_zdjecia_{custom_width}x{custom_height}.zip",
                        mime="application/zip",
                    )


if __name__ == "__main__":
    main()
