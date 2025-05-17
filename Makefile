

setup_local: binary
	@pre-commit install
	@pre-commit install --hook-type pre-commit --hook-type pre-push


start_docker:
	@sudo systemctl start docker

binary:
	@uv sync
	@uv run maturin develop --uv

binary_docker:
	@uv sync --only-group docker
	@uv run maturin develop --uv --release
	@uv sync --no-dev

test: binary
	@uv run coverage run
	@uv run coverage report

lint:
	@uv run ruff check
	@uv run ty check app
