run:
	uvicorn app.main:app --reload

run-api:
	uvicorn app.main:app --reload

demo:
	streamlit run ui/streamlit_app.py

seed:
	python scripts/seed_sample_documents.py

ingest:
	python scripts/ingest_directory.py

eval:
	python scripts/run_local_eval.py

eval-portfolio:
	python scripts/run_local_eval.py --eval-file data/eval/portfolio_eval.jsonl

smoke:
	python scripts/smoke_test.py

reset:
	python scripts/reset_demo_state.py

test:
	python -m unittest discover -s tests -v

ingest-public:
	python scripts/ingest_url_manifest.py --manifest data/corpus/public_service_manifest.csv
