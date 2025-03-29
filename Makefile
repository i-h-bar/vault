setup_local:
	@uv sync
	@maturin develop --uv

setup:
	@uv sync --group docker
	@maturin develop --uv --release

start_docker:
	@sudo systemctl start docker

binary:
	@uv sync
	@uv run maturin develop --uv

binary_docker:
	@uv sync --only-group docker
	@uv run maturin develop --uv --release
	@uv sync --no-dev
