"""
skills_db.py
------------
A curated list of common technical skills, languages, tools, and
frameworks used for keyword-based skill extraction.

Why a hand-curated list instead of something fancier (e.g. asking
an LLM to "find all skills")?
- It's deterministic and free -> same input always gives same output
- It's fast -> no API call per resume
- It's easy to explain and extend in an interview

This list is deliberately not exhaustive. Add more terms here as
needed for your domain (data science, DevOps, etc).
"""

SKILLS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c",
    "go", "golang", "rust", "ruby", "php", "kotlin", "swift", "scala",
    "r", "matlab", "sql", "html", "css", "bash", "shell scripting",

    # Web / backend frameworks
    "react", "react.js", "angular", "vue", "vue.js", "next.js",
    "node.js", "express", "express.js", "django", "flask", "fastapi",
    "spring", "spring boot", ".net", "asp.net", "laravel", "rails",

    # Data / ML / AI
    "machine learning", "deep learning", "nlp",
    "natural language processing", "computer vision", "pandas",
    "numpy", "scikit-learn", "sklearn", "tensorflow", "pytorch",
    "keras", "opencv", "matplotlib", "seaborn", "data analysis",
    "data visualization", "power bi", "tableau", "excel",
    "sentence-transformers", "huggingface", "llm", "generative ai",
    "rag", "vector database", "embeddings",

    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "sqlite",
    "redis", "oracle", "firebase", "dynamodb", "cassandra",

    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes",
    "jenkins", "ci/cd", "terraform", "ansible", "linux", "git",
    "github", "gitlab", "github actions",

    # APIs / architecture
    "rest api", "restful api", "graphql", "microservices",
    "api development", "grpc", "websocket",

    # Tools
    "jira", "figma", "postman", "vs code", "agile", "scrum",

    # Testing
    "unit testing", "pytest", "junit", "selenium", "test automation",

    # Mobile
    "android", "ios", "flutter", "react native",
]

# For each skill, a small set of common alternate spellings/synonyms
# that should count as the same skill when matching.
SYNONYMS = {
    "javascript": ["js"],
    "typescript": ["ts"],
    "node.js": ["nodejs", "node js"],
    "react.js": ["reactjs", "react"],
    "vue.js": ["vuejs", "vue"],
    "next.js": ["nextjs"],
    "express.js": ["expressjs", "express"],
    "postgresql": ["postgres"],
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "natural language processing": ["nlp"],
    "google cloud": ["gcp"],
    "amazon web services": ["aws"],
    "restful api": ["rest api", "rest"],
    "ci/cd": ["cicd", "continuous integration"],
}
