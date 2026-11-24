MASTER PROMPT: BUILD A PRODUCTION-READY AI VOICE-BASED DOCTOR APPOINTMENT BOOKING SYSTEM
ROLE AND RESPONSIBILITY
Act as a Principal Forward Deployed Engineer (FDE), Senior AI Engineer, Software Architect, Backend Engineer, Real-Time Voice Systems Engineer, and Product Designer.
You have extensive industry experience in:
•	Production-grade AI applications.
•	Real-time conversational voice agents.
•	Pipecat voice pipeline development.
•	Speech-to-Text (STT) and Text-to-Speech (TTS).
•	LLMs and function calling.
•	FastAPI and distributed backend systems.
•	React and modern frontend engineering.
•	Database architecture and transaction management.
•	WebRTC and real-time communication.
•	Docker, DevOps, CI/CD, and cloud deployment.
•	Software testing, security, and performance optimization.
Your responsibility is to transform the project requirements below into a complete, functional, professional, production-oriented software product.
Think like an engineer delivering a product to a real client, not an AI assistant generating a coding tutorial.
You must research, architect, implement, test, debug, optimize, and document the complete system.
The final result must be a working application, not just a frontend prototype or a collection of disconnected code snippets.
________________________________________
1. PROJECT OVERVIEW
Project Name
AI-Powered Voice-Based Doctor Appointment Booking System
Product Vision
Build a real-time AI-powered virtual medical receptionist that allows patients to book, check, and cancel doctor appointments using natural voice conversations.
A patient should be able to open the web application, click the "Try Call" button, and speak directly with an AI doctor appointment assistant.
The AI agent should understand the patient's request, identify the required doctor or speciality, check appointment availability, collect the patient's phone number, confirm important details, and execute the requested action.
The system must also provide a professional web dashboard where users can monitor the conversation, view doctors, explore available slots, and manage appointments in real time.
Main Objectives
1.	Build a real-time voice agent using Pipecat.
2.	Integrate ElevenLabs Speech-to-Text.
3.	Integrate ElevenLabs Text-to-Speech.
4.	Integrate Google Gemini as the LLM.
5.	Implement function calling for appointment operations.
6.	Build a robust appointment management backend.
7.	Develop a premium React/Next.js dashboard.
8.	Implement real-time transcript and appointment synchronization.
9.	Provide a realistic phone-style calling experience.
10.	Produce comprehensive engineering documentation in PDF format.
________________________________________
2. COMPLETE TECHNOLOGY STACK
Use the following technologies as the primary stack.
Layer	Technology
Programming language	Python
Voice framework	Pipecat
Speech-to-Text	ElevenLabs STT
Text-to-Speech	ElevenLabs TTS
LLM	Google Gemini
Voice Activity Detection	Silero VAD
Backend framework	FastAPI
Frontend framework	React or Next.js
Frontend language	TypeScript
Styling	Tailwind CSS
UI components	shadcn/ui where appropriate
Database	SQLite initially, PostgreSQL-ready
ORM	SQLAlchemy
Data validation	Pydantic
Real-time communication	WebRTC and WebSocket as appropriate
Testing	Pytest, frontend testing tools
Containerization	Docker and Docker Compose
Version control	Git and GitHub
You may introduce additional libraries if they materially improve the product.
However:
•	Do not introduce unnecessary dependencies.
•	Do not replace the required technologies without explaining why.
•	Verify compatibility between the actual installed package versions.
•	Use official documentation to determine supported APIs and integration methods.
•	Pin compatible dependency versions.
________________________________________
3. DEEP TECHNICAL RESEARCH
Before implementation, conduct comprehensive technical research.
Research the latest compatible documentation and implementation patterns for:
Voice Engineering
•	Pipecat architecture and pipeline lifecycle.
•	Pipecat browser audio transports.
•	ElevenLabs STT integration.
•	ElevenLabs TTS integration.
•	Google Gemini integration.
•	Gemini function calling.
•	Silero VAD.
•	Speech interruption and barge-in.
•	Turn detection and conversational context.
•	Audio streaming and latency optimization.
Backend Engineering
•	FastAPI architecture.
•	Async Python.
•	SQLAlchemy.
•	Database transaction management.
•	WebSocket implementation.
•	Pydantic validation.
•	API versioning.
•	Exception handling.
•	Background processing.
Frontend Engineering
•	React or Next.js architecture.
•	TypeScript.
•	Tailwind CSS.
•	shadcn/ui.
•	WebRTC browser audio.
•	WebSocket integration.
•	Real-time transcript rendering.
•	Audio visualization.
•	Call-state management.
System Engineering
•	WebRTC versus WebSocket trade-offs.
•	Browser-to-Pipecat connectivity.
•	Real-time event synchronization.
•	Concurrent appointment booking.
•	Database consistency.
•	Security and privacy.
•	Docker deployment.
•	Logging and monitoring.
Research Rules
1.	Prioritize official documentation.
2.	Use relevant GitHub repositories and engineering references.
3.	Research current stable versions.
4.	Verify that all integrations are actually supported.
5.	Identify deprecated APIs and incompatible package versions.
6.	Provide source links.
7.	Distinguish verified information from recommendations.
8.	Do not invent API methods, model names, benchmarks, or integration capabilities.
Prepare a technical research report before coding.
________________________________________
4. SYSTEM ARCHITECTURE
Design a modular architecture with clearly separated responsibilities.
The system should contain:
1.	Frontend Dashboard.
2.	Browser Audio Capture.
3.	Real-Time Audio Transport.
4.	Pipecat Voice Pipeline.
5.	Silero VAD.
6.	ElevenLabs STT.
7.	Gemini LLM.
8.	Function Calling and Tool Execution.
9.	Appointment Management Service.
10.	Doctor Availability Service.
11.	ElevenLabs TTS.
12.	Database Layer.
13.	FastAPI Backend.
14.	WebSocket Event Manager.
15.	Real-Time Dashboard Synchronization.
Required Voice Pipeline
Implement the following logical pipeline:
Browser Microphone
→ Audio Transport
→ Silero VAD
→ ElevenLabs STT
→ Gemini LLM
→ Function Calling
→ Backend Business Logic
→ Gemini Response
→ ElevenLabs TTS
→ Browser Audio Output.
The exact pipeline ordering and frame-processing approach must follow the current Pipecat architecture.
Provide architecture diagrams explaining:
•	Audio flow.
•	LLM processing.
•	Tool execution.
•	Database interaction.
•	Frontend/backend communication.
•	Real-time event broadcasting.
Explain how every component communicates with the others.
________________________________________
5. VOICE AGENT IMPLEMENTATION
Build a natural, real-time AI receptionist.
Conversation Requirements
The agent must:
•	Understand natural language.
•	Recognize doctor specialities.
•	Understand appointment dates and times.
•	Maintain conversation context.
•	Ask relevant follow-up questions.
•	Handle interruptions.
•	Handle unclear speech.
•	Repeat important information.
•	Avoid executing actions without required confirmation.
•	Respond naturally and professionally.
•	Handle failures gracefully.
The agent must not pretend an operation succeeded unless the backend confirms success.
Required Function Tools
Implement these three tools inside the Pipecat voice pipeline.
TOOL 1: check_doctor_availability
Purpose: Check available doctors and appointment slots.
Input parameters:
•	doctor_name (optional)
•	speciality (optional)
•	appointment_date (optional)
Expected output:
•	Doctor ID.
•	Doctor name.
•	Speciality.
•	Available dates.
•	Available time slots.
Requirements:
•	Support searches by doctor name.
•	Support speciality-based searches.
•	Support date-based searches.
•	Return structured results.
•	Handle unavailable doctors and dates.
•	Offer alternative slots.
TOOL 2: book_appointment
Purpose: Book a selected appointment for a patient.
Input parameters:
•	patient_phone_number.
•	doctor_id.
•	appointment_date.
•	appointment_time.
•	patient_name, if required by the product workflow.
Requirements:
1.	Collect all required information.
2.	Validate the phone number.
3.	Repeat the number to the patient.
4.	Ask the patient to confirm it.
5.	Confirm the doctor and appointment slot.
6.	Ask for explicit booking confirmation.
7.	Revalidate slot availability.
8.	Execute the database transaction.
9.	Prevent duplicate bookings and double booking.
10.	Return a booking confirmation ID.
11.	Inform the patient of the result.
Do not book an appointment before the patient confirms the details.
TOOL 3: cancel_appointment
Purpose: Cancel an existing appointment using the phone number spoken by the patient.
Input parameters:
•	patient_phone_number.
•	appointment_id (optional).
•	doctor_name (optional).
•	appointment_date (optional).
Requirements:
1.	Collect the patient's phone number.
2.	Repeat the phone number.
3.	Ask for confirmation.
4.	Find matching appointments.
5.	If multiple appointments exist, ask which one to cancel.
6.	Explain which appointment will be cancelled.
7.	Ask for explicit cancellation confirmation.
8.	Execute cancellation.
9.	Update the database.
10.	Return the cancellation result.
Never cancel without explicit confirmation.
Patient Identification Restrictions
The patient is identified only through the phone number spoken during the conversation.
Strictly do not implement:
•	Login.
•	OTP.
•	Caller ID.
•	External identity authentication.
Important security limitation:
A spoken phone number and verbal confirmation do not establish real-world identity. Clearly document the resulting unauthorized-access and cancellation risks. Do not claim that this process securely verifies patient identity.
________________________________________
6. CONVERSATIONAL DESIGN
Create a professional AI receptionist personality.
Example introduction:
"Hello! Welcome to our clinic. I'm your AI appointment assistant. How can I help you today?"
Example availability conversation:
Patient: "I want to see a cardiologist tomorrow."
Agent:
•	Understand the speciality.
•	Check available cardiologists.
•	Retrieve tomorrow's slots.
•	Present available options naturally.
Example booking conversation:
Patient: "Book the 10 AM appointment."
Agent:
•	Confirm the selected doctor.
•	Confirm the date and time.
•	Request the phone number.
•	Repeat the phone number.
•	Ask for confirmation.
•	Execute the booking tool.
•	Provide the booking ID.
Example cancellation conversation:
Patient: "I want to cancel my appointment."
Agent:
•	Request the spoken phone number.
•	Retrieve matching appointments.
•	Ask which appointment to cancel if necessary.
•	Repeat the phone number.
•	Confirm the appointment details.
•	Request explicit cancellation confirmation.
•	Execute cancellation.
•	Confirm the result.
Also handle:
•	Invalid phone numbers.
•	Unavailable slots.
•	Missing information.
•	Multiple matching appointments.
•	LLM failures.
•	STT failures.
•	TTS failures.
•	Database errors.
•	Network disconnections.
•	Patient interruptions.
The agent must not provide medical diagnoses or treatment advice. It is an administrative appointment assistant only.
________________________________________
7. BACKEND DEVELOPMENT
Use FastAPI and build a modular backend.
Required Modules
•	Configuration management.
•	Database connection.
•	SQLAlchemy models.
•	Pydantic schemas.
•	Doctor service.
•	Speciality service.
•	Availability service.
•	Appointment service.
•	Booking service.
•	Cancellation service.
•	Voice agent integration.
•	WebSocket management.
•	Logging and exception handling.
Required Database Entities
Doctor
•	id.
•	name.
•	speciality.
•	experience.
•	description.
•	active status.
Availability
•	id.
•	doctor_id.
•	appointment_date.
•	start_time.
•	end_time.
•	slot_duration.
•	availability_status.
Appointment
•	id.
•	patient_phone_number.
•	patient_name, if collected.
•	doctor_id.
•	appointment_date.
•	appointment_time.
•	status.
•	created_at.
•	updated_at.
Use appropriate foreign keys, constraints, indexes, and relationships.
Database Requirements
•	Persistent appointment storage.
•	Atomic booking transactions.
•	Prevention of double booking.
•	Appropriate cancellation handling.
•	Consistent appointment statuses.
•	Proper timezone handling.
•	Database migrations.
•	Seed data for mock doctors and appointments.
Design the initial SQLite implementation so it can be migrated to PostgreSQL with minimal architectural changes.
________________________________________
8. API DEVELOPMENT
Create documented REST APIs.
Required endpoints should include:
•	GET /api/v1/doctors
•	GET /api/v1/doctors/{doctor_id}
•	GET /api/v1/specialities
•	GET /api/v1/availability
•	POST /api/v1/appointments
•	GET /api/v1/appointments
•	GET /api/v1/appointments/{appointment_id}
•	POST /api/v1/appointments/{appointment_id}/cancel
•	GET /api/v1/dashboard/stats
•	WebSocket endpoint for real-time dashboard events.
Adapt endpoint design where needed.
For every API document:
•	HTTP method.
•	Endpoint.
•	Purpose.
•	Request schema.
•	Response schema.
•	Validation.
•	Error handling.
•	Example request.
•	Example response.
Expose interactive API documentation using FastAPI OpenAPI/Swagger.
________________________________________
9. FRONTEND DASHBOARD
Build a visually exceptional healthcare SaaS dashboard.
Use React or Next.js, TypeScript, and Tailwind CSS.
The design should feel like a professionally designed commercial product.
Avoid:
•	Generic AI-generated dashboard designs.
•	Excessive gradients.
•	Unnecessary animations.
•	Overcrowded cards.
•	Excessive text.
•	Inconsistent spacing.
•	Unnecessary UI elements.
Focus on visual hierarchy, typography, spacing, usability, and responsive design.
Main Dashboard
Display:
•	Total doctors.
•	Available doctors.
•	Total appointments.
•	Confirmed appointments.
•	Cancelled appointments.
•	Recent activity.
Doctor Management
Display:
•	Doctor name.
•	Speciality.
•	Experience.
•	Availability.
•	Available slots.
Appointment Management
Display:
•	Appointment ID.
•	Patient phone number.
•	Doctor.
•	Speciality.
•	Date.
•	Time.
•	Booking status.
•	Cancellation status.
Support useful search, filtering, and status indicators.
Voice Call Interface
When the user clicks "Try Call", open a realistic phone-style call interface.
Required call states:
1.	Idle.
2.	Connecting.
3.	Ringing, if applicable to the connection design.
4.	Connected.
5.	Ended.
6.	Failed or disconnected.
Display:
•	Caller or patient name.
•	AI agent name.
•	Call duration.
•	Connection status.
•	Mute/unmute button.
•	End-call button.
•	Live transcript.
•	User speaking indicator.
•	Agent speaking indicator.
•	Audio waveform.
•	Booking confirmation card.
•	Cancellation confirmation card.
The waveform must respond to actual microphone or audio stream levels rather than simply playing a decorative animation.
Add appropriate transition effects.
Add optional ring and end-call sounds with a mute or sound preference.
Live Transcript
Display the conversation in real time.
Distinguish:
•	Patient messages.
•	AI agent messages.
•	Tool execution events.
•	Booking events.
•	Cancellation events.
Use clear timestamps where appropriate.
Live Dashboard Updates
When the agent successfully books or cancels an appointment:
•	Update appointment rows.
•	Highlight the affected appointment.
•	Update dashboard statistics.
•	Add an activity feed event.
•	Display an in-call confirmation card.
Use WebSockets or an appropriate real-time event mechanism.
________________________________________
10. REAL-TIME COMMUNICATION
Research and select the correct transport architecture for connecting the browser to Pipecat.
Evaluate:
•	WebRTC.
•	WebSocket.
•	Pipecat-supported transports.
Explain the selection based on:
•	Audio latency.
•	Bidirectional communication.
•	Browser compatibility.
•	Implementation complexity.
•	Reliability.
•	Scalability.
Use WebRTC where appropriate for live audio and WebSockets for dashboard events and transcript updates where appropriate.
Do not assume the same transport must handle every communication type.
________________________________________
11. PROJECT STRUCTURE
Create a professional, maintainable folder structure.
Separate:
Backend:
•	app/
•	api/
•	core/
•	database/
•	models/
•	schemas/
•	services/
•	repositories/
•	voice/
•	voice/tools/
•	websocket/
•	tests/
Frontend:
•	app/ or src/
•	components/
•	components/dashboard/
•	components/doctors/
•	components/appointments/
•	components/voice/
•	hooks/
•	services/
•	types/
•	utils/
Infrastructure:
•	Dockerfile.
•	docker-compose.yml.
•	.env.example.
•	requirements.txt or pyproject.toml.
•	package.json.
•	README.md.
•	deployment documentation.
You may adjust this structure based on the architecture, but maintain clean separation of responsibilities.
________________________________________
12. IMPLEMENTATION ROADMAP
Implement the application in the following stages.
Phase 1: Research and Architecture
•	Analyze requirements.
•	Research official documentation.
•	Validate integrations.
•	Choose compatible package versions.
•	Design architecture.
•	Design database.
•	Define APIs.
•	Identify risks.
•	Prepare roadmap.
Phase 2: Backend Foundation
•	Initialize FastAPI.
•	Configure environment.
•	Configure database.
•	Implement models.
•	Implement schemas.
•	Add seed data.
•	Implement doctor APIs.
Phase 3: Appointment Business Logic
•	Implement availability checking.
•	Implement slot generation.
•	Implement booking.
•	Implement cancellation.
•	Add transaction management.
•	Add concurrency protection.
•	Write unit tests.
Phase 4: Pipecat Voice Agent
•	Initialize Pipecat.
•	Integrate transport.
•	Integrate VAD.
•	Integrate ElevenLabs STT.
•	Integrate Gemini.
•	Implement function calling.
•	Integrate ElevenLabs TTS.
•	Implement conversation management.
•	Implement interruptions and error recovery.
Phase 5: Frontend Dashboard
•	Build design system.
•	Build dashboard layout.
•	Build doctor management.
•	Build availability view.
•	Build appointment management.
•	Build phone-call interface.
•	Build live transcript.
•	Build waveform visualization.
Phase 6: Real-Time Integration
•	Connect browser audio.
•	Connect frontend to Pipecat.
•	Implement WebSocket events.
•	Stream transcript updates.
•	Synchronize booking events.
•	Synchronize cancellation events.
Phase 7: Testing and Validation
•	Unit tests.
•	API tests.
•	Database tests.
•	Voice tool tests.
•	Integration tests.
•	Frontend tests.
•	End-to-end tests.
•	Concurrent booking tests.
•	Failure recovery tests.
Phase 8: Production Preparation
•	Configure Docker.
•	Configure environment variables.
•	Implement structured logging.
•	Add health checks.
•	Perform security review.
•	Optimize performance.
•	Prepare deployment.
•	Write complete documentation.
________________________________________
13. END-TO-END ACCEPTANCE TESTS
The finished application must pass these workflows.
Test 1: Doctor Availability
Patient requests a cardiologist for a particular date.
Expected:
•	Correct speciality recognition.
•	Doctor retrieval.
•	Slot retrieval.
•	Natural spoken response.
Test 2: Successful Booking
Patient selects an available slot.
Expected:
•	Phone number collection.
•	Phone number readback.
•	Verbal confirmation.
•	Backend booking execution.
•	Database persistence.
•	Booking ID returned.
•	Dashboard updated.
Test 3: Successful Cancellation
Patient requests cancellation.
Expected:
•	Spoken phone number collection.
•	Appointment lookup.
•	Appointment selection if multiple matches exist.
•	Number confirmation.
•	Explicit cancellation confirmation.
•	Database status updated.
•	Dashboard updated.
Test 4: Unavailable Slot
Expected:
•	No invalid booking.
•	Alternative slots offered.
Test 5: Invalid Phone Number
Expected:
•	Validation error.
•	Agent requests clarification.
•	No booking or cancellation.
Test 6: Concurrent Booking
Two users attempt to book the same slot.
Expected:
•	Only one successful booking.
•	Other request receives an appropriate conflict response.
Test 7: Real-Time Dashboard
During an active call:
Expected:
•	Transcript updates.
•	Agent speaking indicator works.
•	Waveform reacts to real audio.
•	Appointment data updates.
•	Activity feed updates.
Test 8: Service Failure
Simulate an STT, LLM, TTS, or network failure.
Expected:
•	Graceful error handling.
•	Useful user feedback.
•	No false booking confirmation.
•	Appropriate recovery or termination.
________________________________________
14. TESTING AND CODE QUALITY
Follow production engineering practices.
Requirements:
•	Clean architecture.
•	Separation of concerns.
•	Type hints.
•	Pydantic validation.
•	Async operations where appropriate.
•	Meaningful exception handling.
•	Structured logging.
•	Reusable components.
•	Secure configuration.
•	No hardcoded credentials.
•	No unnecessary global state.
•	Proper documentation.
•	Reproducible setup.
Use pytest for backend testing.
Test:
•	Availability logic.
•	Booking logic.
•	Cancellation logic.
•	Phone number validation.
•	Duplicate prevention.
•	Database transactions.
•	Voice tool execution.
•	API integration.
Clearly identify which tests have actually been executed and their results.
________________________________________
15. SECURITY AND PRIVACY
Evaluate:
•	API key protection.
•	Input validation.
•	SQL injection prevention.
•	CORS configuration.
•	Secure transport.
•	Environment variable management.
•	Logging of sensitive data.
•	Patient phone number exposure.
•	Data retention.
•	Database backups.
•	Rate limiting.
•	Dependency vulnerabilities.
Do not log complete phone numbers unnecessarily.
Document the security limitations caused by identifying patients solely through spoken phone numbers.
Do not represent this prototype's spoken-number confirmation as secure identity authentication.
The application is an administrative appointment booking assistant, not a medical diagnosis system.
________________________________________
16. DEVOPS AND DEPLOYMENT
Provide:
•	Backend Dockerfile.
•	Frontend Dockerfile if appropriate.
•	Docker Compose.
•	Environment configuration.
•	Database initialization.
•	Health checks.
•	CI/CD recommendations.
•	Production deployment instructions.
•	Logging configuration.
•	Monitoring recommendations.
•	Rollback strategy.
Provide exact commands for:
1.	Environment setup.
2.	Dependency installation.
3.	Database initialization.
4.	Backend startup.
5.	Frontend startup.
6.	Running tests.
7.	Docker startup.
8.	Production deployment.
The application must be easy to run locally.
________________________________________
17. PERFORMANCE AND RELIABILITY
Evaluate:
•	Voice pipeline latency.
•	STT processing time.
•	LLM response time.
•	TTS generation time.
•	End-to-end response latency.
•	WebSocket reliability.
•	Concurrent connections.
•	Database performance.
•	Appointment transaction reliability.
Define performance targets before testing.
Measure actual results and identify bottlenecks.
Do not fabricate benchmarks or claim optimizations without verification.
________________________________________
18. FINAL PDF ENGINEERING DOCUMENTATION
Create a comprehensive professional PDF document.
Document Title
AI Voice-Based Doctor Appointment Booking System: Complete Technical Research, Architecture, Implementation and Deployment Guide
The PDF must include:
1.	Executive summary.
2.	Product vision.
3.	Problem statement.
4.	Functional requirements.
5.	Non-functional requirements.
6.	Technology stack analysis.
7.	Technical research.
8.	Official documentation references.
9.	System architecture.
10.	Voice pipeline architecture.
11.	Audio transport architecture.
12.	Function calling architecture.
13.	Database ER diagram.
14.	Database schema.
15.	API specifications.
16.	Complete project structure.
17.	Step-by-step backend implementation.
18.	Step-by-step Pipecat implementation.
19.	ElevenLabs integration.
20.	Gemini integration.
21.	Silero VAD integration.
22.	Frontend implementation.
23.	Phone-call UI implementation.
24.	Real-time communication.
25.	Booking and cancellation workflows.
26.	Testing strategy.
27.	Security considerations.
28.	Docker configuration.
29.	Deployment instructions.
30.	Troubleshooting.
31.	Performance evaluation.
32.	Production readiness checklist.
33.	Future improvements.
34.	References.
PDF QUALITY
The PDF must have:
•	Professional technical-document design.
•	Cover page.
•	Table of contents.
•	Consistent typography.
•	Proper section hierarchy.
•	Page numbers.
•	Headers and footers.
•	Readable code blocks.
•	Architecture diagrams.
•	Workflow diagrams.
•	Database tables.
•	API tables.
•	Clickable references.
•	Clear implementation instructions.
Do not produce a shallow summary.
The document must be detailed enough for another engineer to reproduce the project from scratch.
________________________________________
19. FDE ENGINEERING EXPECTATIONS
Act as an engineer responsible for delivering a product to a client.
Follow these principles:
1.	Understand the business problem before coding.
2.	Research before selecting implementation patterns.
3.	Design before implementing.
4.	Keep the client informed about technical decisions.
5.	Explain trade-offs.
6.	Build incrementally.
7.	Test each module.
8.	Debug actual failures.
9.	Verify integrations.
10.	Deliver reproducible code.
11.	Maintain technical documentation.
12.	Clearly communicate limitations.
Do not generate the entire project as a single unstructured code dump.
Maintain a project implementation checklist and track:
•	Not started.
•	In progress.
•	Implemented.
•	Tested.
•	Verified.
Never mark a task as tested or verified unless it has actually been tested.
________________________________________
20. WORKING MODE — IMPORTANT
Do not immediately start coding.
Work in the following order:
STEP 1 — Requirement Analysis
Analyze every requirement and identify missing details, assumptions, constraints, and risks.
STEP 2 — Technical Research
Research the current documentation and verify compatibility of all required technologies.
STEP 3 — Architecture Design
Create architecture diagrams, component responsibilities, data flows, and database design.
STEP 4 — Implementation Roadmap
Create a detailed, dependency-aware development roadmap.
STEP 5 — Client Review
Present the research findings, architecture, technology decisions, and roadmap.
Wait for my approval before beginning the main implementation.
STEP 6 — Incremental Development
Implement one module at a time. Provide complete code, commands, explanations, and tests.
STEP 7 — Integration and Testing
Connect all components and validate the complete end-to-end workflows.
STEP 8 — Final Delivery
Deliver the working source code, README, deployment configuration, test results, and comprehensive PDF engineering guide.
________________________________________
FINAL SUCCESS CRITERIA
The project is complete only when:
•	The browser can establish a real voice session.
•	The Pipecat pipeline processes live audio.
•	ElevenLabs STT works.
•	Gemini understands the conversation.
•	Function calling executes real backend tools.
•	ElevenLabs TTS generates spoken responses.
•	Availability checking works.
•	Booking works and persists in the database.
•	Cancellation works and persists in the database.
•	Phone-number readback and confirmation are enforced.
•	Double booking is prevented.
•	The dashboard displays live transcripts.
•	The phone-style call interface works.
•	Appointment data updates in real time.
•	Tests are executed and documented.
•	Setup and deployment instructions are reproducible.
•	The complete professional PDF guide is generated.
ULTIMATE OBJECTIVE:
Deliver a complete, working, scalable, maintainable, and professionally designed AI voice-based doctor appointment booking system that demonstrates real-world Forward Deployed Engineering capabilities.
The final product must be something I can confidently demonstrate to a client, explain in a technical interview, and extend into a commercial application.
Execution instruction: Start with requirement analysis, technical research, architecture diagrams, and an implementation roadmap. Wait for my approval before coding.

