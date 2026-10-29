import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


MODEL_ID = "jncraton/m2m100_418M-ct2-int8"
MODEL_REVISION = "7c1b2620a4e58dacecbd8bf89cfd6da7eb9eb7b0"
MODEL_FILES = ["config.json", "model.bin", "shared_vocabulary.json", "sentencepiece.bpe.model"]
DEPENDENCIES = ("ctranslate2", "sentencepiece", "huggingface_hub")


def ensure_dependencies():
    missing = [name for name in DEPENDENCIES if importlib.util.find_spec(name) is None]
    if not missing:
        return
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Activate your virtual environment first: source .venv/bin/activate")
    requirements = Path(__file__).with_name("requirements-local.txt")
    print("Installing local translation dependencies in the active environment...", flush=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(requirements)],
        check=True,
    )
    importlib.invalidate_caches()


class LocalTranslator:
    def __init__(self):
        ensure_dependencies()
        import ctranslate2
        import sentencepiece
        from huggingface_hub import snapshot_download
        from huggingface_hub.errors import LocalEntryNotFoundError

        options = dict(repo_id=MODEL_ID, revision=MODEL_REVISION, allow_patterns=MODEL_FILES)
        try:
            model_path = Path(snapshot_download(**options, local_files_only=True))
            if not all((model_path / filename).is_file() for filename in MODEL_FILES):
                raise FileNotFoundError("Incomplete model cache")
        except (LocalEntryNotFoundError, FileNotFoundError):
            print("Downloading local M2M100 INT8 model (~496 MB, first use only)...", flush=True)
            model_path = Path(snapshot_download(**options))

        print("Loading local M2M100 INT8 model...", flush=True)
        self.tokenizer = sentencepiece.SentencePieceProcessor(
            model_file=str(model_path / "sentencepiece.bpe.model")
        )
        with (model_path / "shared_vocabulary.json").open(encoding="utf-8") as vocabulary_file:
            self.vocabulary = set(json.load(vocabulary_file))
        self.translator = ctranslate2.Translator(str(model_path), device="cpu", compute_type="int8")

    def translate_batch(self, items, culture):
        translations = [""] * len(items)
        to_translate = [(index, text) for index, text in enumerate(items)
                        if text not in ("[Empty]", "[Missing]", "")]
        if not to_translate:
            return translations
        source_code = culture.split("-")[0].lower()
        if source_code == "en":
            for index, text in to_translate:
                translations[index] = text
            return translations
        source_token = f"__{source_code}__"
        try:
            if source_token not in self.vocabulary:
                raise ValueError(f"Unsupported language: {culture}")
            encoded = [[source_token] + self.tokenizer.encode(text, out_type=str) + ["</s>"]
                       for index, text in to_translate]
            results = self.translator.translate_batch(
                encoded,
                target_prefix=[["__en__"] for index, text in to_translate],
                beam_size=2,
                max_batch_size=16,
                max_input_length=1024,
                max_decoding_length=256,
            )
            for (index, text), result in zip(to_translate, results):
                tokens = [token for token in result.hypotheses[0]
                          if token not in ("__en__", "<s>", "</s>", "<pad>")]
                translations[index] = self.tokenizer.decode(tokens)
        except Exception as error:
            print(f"\n  [Local translation error for {culture}: {error}]")
            for index, text in to_translate:
                translations[index] = "Local translation unavailable"
        return translations