class BaseConfig:

    RASA_URL = "http://localhost:5005/model/parse"

    CONFIDENCE_HIGH = 0.60
    CONFIDENCE_MEDIUM = 0.40

    HANDOFF_KEYWORDS = ["agent", "human", "manager", "support", "customer care"]
