#!/bin/bash
pip install crewai==0.150.0
uvicorn main:app --host 0.0.0.0 --port $PORT
