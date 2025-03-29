setup_local:
	@uv sync
	@maturin develop --uv

setup:
	@uv sync --group docker
	@maturin develop --uv --release
