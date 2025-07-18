# run_pipeline.py
import os
import json
from pipeline.graph import create_pipeline


def process_pdf_with_metadata(pdf_path: str):
    """
    Main function to process a PDF and extract values with metadata.
    """
    print("=" * 60)
    print("PDF TABLE EXTRACTION WITH METADATA")
    print("=" * 60)

    # Create the pipeline
    app = create_pipeline()

    # Initial state
    initial_state = {
        "pdf_path": pdf_path
    }

    # Run the pipeline
    print("\n🚀 RUNNING PIPELINE...")
    final_state = app.invoke(initial_state)

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

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

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
    # Process the PDF
    pdf_file = "data/Table-Example-R.pdf"

    if not os.path.exists(pdf_file):
        print(f"❌ ERROR: PDF not found at {pdf_file}")
    else:
        process_pdf_with_metadata(pdf_file)