from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    #log_id="log_1234",
    flag="TracingCore",
    file_name="tracing_core.py",
    show_info_logs=True,
    show_metadata=True,
    save_logs=True,
    format_metadata=False
)

tracer.INFO(
    func_name="create_user",
    message="App Init"
)

tracer.DEBUG(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"},
    #save_logs=False
    #show_metadata=False  # override LOCAL
)

tracer.WARNING(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"},
)

tracer.ERROR(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"},
)

tracer.CRITICAL(
    func_name="create_user",
    message="User created",
    metadata={"user": "Enzo"},
)

# python -m src.tracing.tracing_test