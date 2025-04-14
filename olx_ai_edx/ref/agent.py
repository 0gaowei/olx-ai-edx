import json
import autogen
import os
os.environ["AUTOGEN_USE_DOCKER"] = "no"  # 禁用 Docker
from typing import Dict, List, Any

# Configuration for agents
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": os.getenv("OPENAI_API_KEY"),  # 从环境变量读取
    }
]

# Create a user proxy agent that will execute code and provide feedback
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: "TASK COMPLETE" in x.get("content", ""),
    code_execution_config={"work_dir": "course_generation"},
)

# Create a course designer agent for generating content
course_designer = autogen.AssistantAgent(
    name="CourseDesigner",
    system_message="""You are an expert course designer specializing in creating educational content.
You can generate well-structured course outlines and detailed lesson content based on user requirements.
You focus on logical progression of concepts, clear explanations, and appropriate content for the user's level.""",
    llm_config={"config_list": config_list},
)

# Create a reviewer agent to evaluate and improve content
course_reviewer = autogen.AssistantAgent(
    name="CourseReviewer",
    system_message="""You are an expert course reviewer with experience in educational content evaluation.
Your job is to critically analyze course outlines and content, looking for gaps, inconsistencies, 
or areas that could be improved. Provide specific, actionable feedback.""",
    llm_config={"config_list": config_list},
)


class CourseGenerationAgent:
    def __init__(self):
        self.course_outline = {}
        self.course_content = {}

    def run(self, skill_req: str, user_level: str, learning_obj: str):
        """Main function to run the course generation pipeline"""
        print(f"Starting course generation for {skill_req} at {user_level} level")

        # Stage 1: Generate course outline
        self._generate_course_outline(skill_req, user_level, learning_obj)

        # Stage 2: Generate detailed content for each chapter
        self._generate_chapter_contents()

        # Stage 3: Review entire course
        self._review_entire_course()

        # Save final course
        self._save_course()

        return self.course_content

    def _generate_course_outline(self, skill_req: str, user_level: str, learning_obj: str):
        """Stage 1: Generate and refine course outline"""
        print("Stage 1: Generating course outline...")

        # Generate initial outline
        user_proxy.initiate_chat(
            course_designer,
            message=f"""
            You are a course design expert. Based on the following user information, generate a detailed course outline:
            - User skill requirement: {skill_req}
            - User level: {user_level}
            - Learning objective: {learning_obj}

            Output a JSON format outline with at least 10 chapters, each with a title and short description.
            Format should be:
            {{
              "course_title": "Course Title - User Name",
              "chapters": [
                {{"title": "Chapter 1: Title", "description": "Description text"}},
                ...
              ]
            }}
            """
        )

        # Extract the JSON from last message
        outline_json = self._extract_json_from_message(user_proxy.last_message()["content"])

        # Review and refine outline (2 iterations)
        for i in range(2):
            print(f"Reviewing outline - iteration {i + 1}...")
            user_proxy.initiate_chat(
                course_reviewer,
                message=f"""
                You are a course review expert. Review the following course outline, checking if it's comprehensive,
                logically structured, and appropriate for {user_level} level users:

                {json.dumps(outline_json, indent=2)}

                Output your review comments including specific improvement suggestions.
                """
            )

            review_comments = user_proxy.last_message()["content"]

            # Update outline based on review
            user_proxy.initiate_chat(
                course_designer,
                message=f"""
                Based on the following review comments, update the course outline:

                Current outline: {json.dumps(outline_json, indent=2)}

                Review comments: {review_comments}

                Output the updated JSON outline.
                """
            )

            # Update the outline
            outline_json = self._extract_json_from_message(user_proxy.last_message()["content"])

        self.course_outline = outline_json
        print(f"Course outline generated with {len(self.course_outline.get('chapters', []))} chapters")

    def _generate_chapter_contents(self):
        """Stage 2: Generate detailed content for each chapter"""
        print("Stage 2: Generating chapter contents...")

        self.course_content = {
            "course_title": self.course_outline.get("course_title", ""),
            "chapters": []
        }

        for idx, chapter in enumerate(self.course_outline.get("chapters", [])):
            print(f"Generating content for Chapter {idx + 1}: {chapter['title']}")

            # Generate initial content
            user_proxy.initiate_chat(
                course_designer,
                message=f"""
                You are a course design expert. Generate detailed content for the following chapter:

                - Chapter title: {chapter['title']}
                - Chapter description: {chapter['description']}
                - User level: {self.course_outline.get('user_level', 'beginner')}

                Output JSON format with at least 2 sequentials (units), each with 1 vertical (lesson),
                containing HTML content and a quiz question.

                Format:
                {{
                  "chapter_title": "{chapter['title']}",
                  "sequentials": [
                    {{
                      "title": "Unit 1: Title",
                      "verticals": [
                        {{
                          "html": "<p>Content here...</p>",
                          "problem": "<problem><p>Quiz question?</p><choiceresponse><choice>Answer</choice></choiceresponse></problem>"
                        }}
                      ]
                    }},
                    ...
                  ]
                }}
                """
            )

            chapter_content = self._extract_json_from_message(user_proxy.last_message()["content"])

            # Review and refine chapter content
            user_proxy.initiate_chat(
                course_reviewer,
                message=f"""
                You are a course review expert. Review the following chapter content, checking if it's
                appropriate for the target level, comprehensive, and engaging:

                {json.dumps(chapter_content, indent=2)}

                Output your review comments with specific improvement suggestions.
                """
            )

            review_comments = user_proxy.last_message()["content"]

            # Update content based on review
            user_proxy.initiate_chat(
                course_designer,
                message=f"""
                Based on the following review comments, update the chapter content:

                Current content: {json.dumps(chapter_content, indent=2)}

                Review comments: {review_comments}

                Output the updated JSON content.
                """
            )

            # Update the chapter content
            chapter_content = self._extract_json_from_message(user_proxy.last_message()["content"])
            self.course_content["chapters"].append(chapter_content)

            print(f"Content generated for Chapter {idx + 1} with {len(chapter_content.get('sequentials', []))} units")

    def _review_entire_course(self):
        """Stage 3: Review the entire course for consistency and completeness"""
        print("Stage 3: Reviewing entire course...")

        # Review entire course
        user_proxy.initiate_chat(
            course_reviewer,
            message=f"""
            You are a course review expert. Review the following complete course, checking for:
            - Chapter transitions and flow
            - Content depth and appropriateness
            - Overall alignment with learning objectives

            Course Content: {json.dumps(self.course_content, indent=2, ensure_ascii=False)}

            Output your review comments with specific improvement suggestions for the entire course.
            """
        )

        review_comments = user_proxy.last_message()["content"]

        # Update course based on review
        user_proxy.initiate_chat(
            course_designer,
            message=f"""
            Based on the following review comments, update the entire course:

            Review comments: {review_comments}

            Note: You don't need to output the entire course again, just describe the changes
            you would make to address each review point.
            """
        )

        update_suggestions = user_proxy.last_message()["content"]

        # Apply updates (in a real system, this would update the actual content)
        print("Updates to apply based on final review:")
        print(update_suggestions)

    def _save_course(self):
        """Save the final course to a JSON file"""
        with open("final_course.json", "w", encoding="utf-8") as f:
            json.dump(self.course_content, f, indent=2, ensure_ascii=False)
        print("Final course saved to 'final_course.json'")

    def _extract_json_from_message(self, message: str) -> Dict:
        """Helper function to extract JSON from message text"""
        try:
            # Find code blocks containing JSON
            if "```json" in message:
                json_blocks = message.split("```json")
                if len(json_blocks) > 1:
                    json_content = json_blocks[1].split("```")[0].strip()
                    return json.loads(json_content)

            # Try to find JSON objects directly
            start_idx = message.find("{")
            end_idx = message.rfind("}")

            if start_idx != -1 and end_idx != -1:
                json_content = message[start_idx:end_idx + 1]
                return json.loads(json_content)

            # Fallback: Try to parse the entire message
            return json.loads(message)
        except json.JSONDecodeError:
            print("Warning: Failed to extract valid JSON. Returning empty dict.")
            return {}


def main():
    # Example usage
    course_generator = CourseGenerationAgent()
    course = course_generator.run(
        skill_req="Python programming",
        user_level="beginner",
        learning_obj="Master Python basics"
    )

    print("\nTASK COMPLETE: Course generation finished")
    print(f"Generated course: {course['course_title']}")
    print(f"Total chapters: {len(course['chapters'])}")


if __name__ == "__main__":
    main()