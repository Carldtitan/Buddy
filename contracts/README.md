# Buddy Shared Contracts

These schemas are the source of truth for every Buddy service:

- React Native app payloads
- FastAPI backend orchestration
- Runpod Flash reasoning endpoints
- Runpod voice worker transcript output
- Community report rendering

The Python contracts live in `buddy_contracts.py`. Keep API responses compatible with
these models so the app can swap mock services for real Bright Data, Twilio, and
Runpod services without changing UI code.
