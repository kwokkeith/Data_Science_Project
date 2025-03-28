## Overview
This project aims to perform prediction of American Sign Language. It is capable of classifying gestures by first categorising it as either static or dynamic actions. It then passes the raw frames to either a static or dynamic model for prediction of the gesture. For tinkering, the model also passes these predictions into a small Large-Language Model to perform english sentence formations.

### Model Structure Summary:
1. Classification Model: Logistic Regression on Weighted Average Movement
2. Action Recognition (Dynamic) Model: Long-short Term Memory Neural Network
3. Alphabet Recognition (Static) Model: Feed Forward Neural Network
4. English Structure (LLM) Model: Llama Large Language Model

Predictions:
Static Gestures: [A-Z,0-9]
Dynamic Gestures: ["Hello", "My", "Name", "Your", "What"]

A Grammar in Backus–Naur form was curated to guide the small Large-Language Model in structuring the English sentences.
```gbnf
root                   ::= statement | question | greeting-question | greeting-statement 

question               ::= interrogative-pronoun WS verb WS possessive-pronoun WS noun "?"
greeting-question      ::= greeting WS question
statement              ::= possessive-pronoun WS noun WS verb WS proper-noun (WS proper-noun)*
greeting-statement     ::= greeting WS statement

greeting               ::= "hello"
interrogative-pronoun  ::= "what"
possessive-pronoun     ::= "my" | "your"
verb                   ::= "is"
noun                   ::= "name"

proper-noun            ::= lowercase-letter+
lowercase-letter       ::= [a-z]
number	      	       ::= [0-9]
WS                     ::= " " | "\t" | "\n"
```

### Project Folder Structures:
1. action\_detection: Dynamic Gesture Model codebase
2. alphabet\_detection\_model: Static Gesture Model codebase
3. classification\_model: Static/Dynamic Classification Model codebase
4. combined: The chained model (whole pipeline)

## Preinstallation
A requirements.txt is provided for both mac and linux version. It is unclear if these requirements are sufficient or compatible for windows users.

These requirements are required to run this project in the appropriate environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt # For Linux
pip install -r requirements_mac.txt # For Mac
```

## Authors
This project was completed as part of the Singapore University of Technology and Design's 50.038 Computational Data Science module.
1. Kwok Keith
2. Gizelle Lim Yin Xuan
3. Jun Kiat Lim
