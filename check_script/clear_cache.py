from backend.database import clear_llm_cache

if __name__ == "__main__":
    print("Clearing persistent LLM cache...")
    clear_llm_cache()
    print("Done.")
