FROM mcr.microsoft.com/devcontainers/base:ubuntu

USER vscode
WORKDIR /home/vscode

# Elan selects the exact Lean release recorded in the repository's lean-toolchain file.
RUN curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y --default-toolchain none

ENV PATH="/home/vscode/.elan/bin:${PATH}"

