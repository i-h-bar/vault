setup_local:
	@uv sync
	@maturin develop --uv

setup:
	@uv sync
	@maturin develop --uv --release