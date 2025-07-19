# run_pipeline.py
import os
import json

# --- THE FIX IS HERE ---
# We MUST load the .env file at the very beginning of the script,
# so that the OPENAI_API_KEY is available when other modules are imported.
from dotenv import load_dotenv
load_dotenv()
# --- END OF FIX ---

# Now we can import the pipeline components
from pipeline.graph import create_pipeline


def process_pdf_with_metadata(pdf_path: str):
    """
    Main function to process a PDF and extract values with metadata.
    """
    print("=" * 60)
    print("PDF TABLE EXTRACTION WITH METADATA (Multimodal AI)")
    print("=" * 60)

    # Create the pipeline
    app = create_pipeline()

    # Initial state
    initial_state = {
        "pdf_path": pdf_path
    }

    # Run the pipeline
    print("\n🚀 RUNNING PIPELINE...")
    try:
        final_state = app.invoke(initial_state)
    except Exception as e:
        print("\n" + "="*20 + " FATAL PIPELINE ERROR " + "="*20)
        print(f"An error occurred during the pipeline execution: {e}")
        print("Please check your OpenAI API key, account balance, and network connection.")
        print("="*64)
        return None

    # Get results
    results = final_state.get("values_with_metadata", [])

    # Save results
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "values_with_metadata.json")

    output_data = {
        "source_pdf": pdf_path,
        "total_values": len(results),
        "values": results
    }

    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ SUCCESS!")
    print(f"📁 Results saved to: {output_path}")
    print(f"📊 Total values with metadata: {len(results)}")

    # Show sample
    if results:
        print("\n📋 SAMPLE RESULT:")
        print("-" * 40)
        sample = results[0]
        print(f"Value: {sample['value']}")
        print(f"Row headers: {' > '.join(sample['row_headers'])}")
        print(f"Column headers: {' > '.join(sample['column_headers'])}")

    return results


if __name__ == "__main__":
    # Ensure you have python-dotenv installed: pip install python-dotenv
    pdf_file = "data/Table-Example-R.pdf"

    if not os.path.exists(pdf_file):
        print(f"❌ ERROR: PDF not found at {pdf_file}")
    else:
        process_pdf_with_metadata(pdf_file)