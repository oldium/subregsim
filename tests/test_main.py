"""Tests for the command-line options."""
import sys

from subregsim.__main__ import parse_command_line


def parse(monkeypatch, *args):
    monkeypatch.delenv("SUBREGSIM_DOMAIN", raising=False)
    monkeypatch.setattr(sys, "argv", ["subregsim", *args])
    return parse_command_line()


def test_domain_defaults_to_example_com(monkeypatch):
    assert parse(monkeypatch).domains == ["example.com"]


def test_domain_option_replaces_the_default(monkeypatch):
    assert parse(monkeypatch, "--domain", "example.org").domains == ["example.org"]


def test_repeated_domain_options_are_all_kept(monkeypatch):
    args = ("--domain", "example.org", "--domain", "example.net")
    assert parse(monkeypatch, *args).domains == ["example.org", "example.net"]
