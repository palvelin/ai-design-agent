from .update_knowledge_base import update_knowledge_markdown

def main():
    update_knowledge_markdown(
        db_path="data/papers_structured.jsonl",
        knowledge_dir="knowledge",
    )

if __name__ == "__main__":
    main()