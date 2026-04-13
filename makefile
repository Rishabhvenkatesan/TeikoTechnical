.PHONY: setup pipeline dashboard

setup:
	pip install -r requirements.txt

pipeline:
	python load_data.py
	python frequency.py
	python stats_analysis.py
	python subset_analysis.py

dashboard:
	python dashboard.py