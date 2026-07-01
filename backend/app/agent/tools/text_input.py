class TextInputTool:
    def normalize(self, text: str) -> str:
        normalized = "\n".join(line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"))
        normalized = "\n".join(line for line in normalized.split("\n") if line)
        if not normalized:
            raise ValueError("Empty input text")
        return normalized
