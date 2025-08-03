#!/bin/bash
pip install crewai==0.150.0
crewai run
uvicorn main:app --host 0.0.0.0 --port $PORT
