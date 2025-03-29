setup_local:
	@uv sync
	@maturin develop --uv

setup:
	@uv sync
	@maturin develop --uv --release
	@pre-commit install

start_docker:
	@sudo systemctl start docker

binary:
	@uv sync
	@uv run maturin develop --uv

binary_docker:
	@uv sync --only-group docker
	@uv run maturin develop --uv --release
	@uv sync --no-dev
