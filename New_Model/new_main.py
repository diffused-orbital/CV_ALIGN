# !pip install PyPDF2
# !pip install python-docx
# !pip install langchain_google_genai
# !pip install sentence_transformers
import os
from functions import scoring as sc
os.environ["GOOGLE_API_KEY"] = "AIzaSyCQwcOs4gYRDS2Iw-_b3DivFcIuVT6zVhw"

if __name__ == "__main__":
    resume_folder = "/content/Company A/resumes"
    jd_file = "/content/Company A/NLP Data Scientist - Hydroscope.pdf"
    
    ranked_results = sc.process_resumes(resume_folder, jd_file)
    print("\n🏆 Final Ranking 🏆\n")
    for rank, result in enumerate(ranked_results, start=1):
        print(f"Rank {rank}: {result['Name']} - Score: {result['Score']:.2f}/100")
        print("Feedback:")
        print(result["Feedback"])
        print("=" * 50)