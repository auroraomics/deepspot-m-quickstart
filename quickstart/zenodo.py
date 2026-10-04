"""Fetch one member of the example archive, without downloading the archive.

The example data is one published archive. The notebooks need one slide from
it, so this module reads the archive's index over two small range requests and
streams only that member to disk, checking its stored checksum as it arrives.

The file name, its size and its download URL come from the Zenodo record, and
the member offsets from the archive's own index.

    python -m quickstart.zenodo --list
    python -m quickstart.zenodo slide

Data source
-----------
Dawo, S., Nonchev, K., & Silina, K. (2025). *10x Visium Spatial
Transcriptomics Dataset: Kidney (3) and Lung (5) Cancer with Tertiary Lymphoid
Structures* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.14620362
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import httpx

RECORD_ID = "14620362"
"""The Zenodo record. Everything else about the archive is read from it."""

DOI = "10.5281/zenodo.14620362"
CITATION = (
    "Dawo, S., Nonchev, K., & Silina, K. (2025). 10x Visium Spatial "
    "Transcriptomics Dataset: Kidney (3) and Lung (5) Cancer with Tertiary "
    "Lymphoid Structures [Data set]. Zenodo. "
    "https://doi.org/10.5281/zenodo.14620362"
)

SAMPLE = "LC1"
"""The lung cancer section the notebooks use.

The archive holds five lung and three kidney sections; pass ``sample=`` (or
``--sample``) to fetch another.
"""

ROLES = {
    "slide": r"tif_slides/{sample}\.tif$",
}
"""What the notebooks ask for, as a pattern over the archive's own index.

`slide` is the H&E image the prediction is made from. The patterns are matched
case-insensitively against the full member name.
"""

DEFAULT_DEST = Path(__file__).resolve().parent.parent / "data"

_EOCD = b"PK\x05\x06"
_EOCD64_LOCATOR = b"PK\x06\x07"
_EOCD64 = b"PK\x06\x06"
_CENTRAL = b"PK\x01\x02"
_MAX_COMMENT = 65535
_DEFLATED = 8
_STORED = 0


class ArchiveIndexError(RuntimeError):
    """The published archive is not shaped the way this module can read."""


@dataclass(frozen=True)
class Member:
    """One member of the archive, as its index describes it."""

    name: str
    compressed_size: int
    size: int
    method: int
    header_offset: int
    crc: int

    @property
    def basename(self) -> str:
        return self.name.rsplit("/", 1)[-1]


@dataclass(frozen=True)
class Archive:
    """The published archive: where it is, how large, and what is in it."""

    url: str
    filename: str
    size: int
    members: tuple[Member, ...]

    def matching(self, pattern: str) -> Member:
        """The one member whose name matches, or a refusal that says why.

        One member, never the first of several: a pattern that matches two
        files is a pattern that has stopped meaning what its author thought,
        and silently taking one of them is how a notebook starts reading the
        wrong section.
        """
        rule = re.compile(pattern, re.IGNORECASE)
        found = [m for m in self.members if rule.search(m.name)]
        if not found:
            raise ArchiveIndexError(
                f"no member of {self.filename} matches {pattern!r}. "
                f"Run `python -m quickstart.zenodo --list` to see what it holds."
            )
        if len(found) > 1:
            names = ", ".join(m.name for m in found[:5])
            raise ArchiveIndexError(
                f"{len(found)} members of {self.filename} match {pattern!r}: "
                f"{names}. Narrow the pattern rather than taking one of them."
            )
        return found[0]


def role_pattern(role: str, sample: str = SAMPLE) -> str:
    """The index pattern for one role, built from the sample name."""
    try:
        return ROLES[role].format(sample=re.escape(sample))
    except KeyError:
        raise ArchiveIndexError(
            f"{role!r} is not a role this module knows. Known: "
            f"{', '.join(sorted(ROLES))}."
        ) from None


def record(client: httpx.Client | None = None) -> dict:
    """The Zenodo record, as published."""
    owns = client is None
    client = client or httpx.Client(timeout=60.0, follow_redirects=True)
    try:
        response = client.get(f"https://zenodo.org/api/records/{RECORD_ID}")
        response.raise_for_status()
        return response.json()
    finally:
        if owns:
            client.close()


def _range(client: httpx.Client, url: str, start: int, end: int) -> bytes:
    """Bytes ``start`` to ``end`` inclusive, or a refusal that names the cause."""
    response = client.get(url, headers={"Range": f"bytes={start}-{end}"})
    if response.status_code != 206:
        raise ArchiveIndexError(
            f"the host answered {response.status_code} to a range request, so "
            "the archive's index cannot be read without downloading all of it. "
            f"Download {url} by hand and unpack the members you need."
        )
    return response.content


def _central_directory_bounds(tail: bytes, archive_size: int) -> tuple[int, int]:
    """Where the index starts and how long it is, from the archive's footer."""
    at = tail.rfind(_EOCD)
    if at < 0:
        raise ArchiveIndexError("no end-of-central-directory record in the footer")
    _, _, _, _, _, size, offset, _ = struct.unpack("<IHHHHIIH", tail[at : at + 22])

    # An archive over 4 GiB, or with over 65,535 members, writes the real
    # numbers in a second footer and leaves these as all-ones markers.
    if offset == 0xFFFFFFFF or size == 0xFFFFFFFF:
        at64 = tail.rfind(_EOCD64)
        if at64 < 0:
            raise ArchiveIndexError(
                "the footer marks a 64-bit archive and carries no 64-bit record"
            )
        size = struct.unpack("<Q", tail[at64 + 40 : at64 + 48])[0]
        offset = struct.unpack("<Q", tail[at64 + 48 : at64 + 56])[0]

    if offset + size > archive_size:
        raise ArchiveIndexError("the footer points past the end of the archive")
    return offset, size


def _parse_central_directory(raw: bytes) -> tuple[Member, ...]:
    members: list[Member] = []
    at = 0
    while at < len(raw) and raw[at : at + 4] == _CENTRAL:
        fields = struct.unpack("<IHHHHHHIIIHHHHHII", raw[at : at + 46])
        method, crc = fields[4], fields[7]
        csize, size = fields[8], fields[9]
        name_len, extra_len, comment_len = fields[10], fields[11], fields[12]
        header_offset = fields[16]
        name = raw[at + 46 : at + 46 + name_len].decode("utf-8", "replace")
        members.append(Member(name, csize, size, method, header_offset, crc))
        at += 46 + name_len + extra_len + comment_len
    if not members:
        raise ArchiveIndexError("the index held no members")
    return tuple(members)


def index(client: httpx.Client | None = None) -> Archive:
    """Read the published archive's index. Two range requests, no bulk transfer."""
    owns = client is None
    client = client or httpx.Client(timeout=120.0, follow_redirects=True)
    try:
        files = record(client).get("files", [])
        if len(files) != 1:
            raise ArchiveIndexError(
                f"record {RECORD_ID} publishes {len(files)} files; this module "
                "reads a record that publishes exactly one archive."
            )
        entry = files[0]
        url = entry["links"]["self"]
        size = int(entry["size"])

        footer = _range(client, url, max(0, size - _MAX_COMMENT - 22), size - 1)
        offset, length = _central_directory_bounds(footer, size)
        raw = _range(client, url, offset, offset + length - 1)
        return Archive(url, entry["key"], size, _parse_central_directory(raw))
    finally:
        if owns:
            client.close()


def _member_data_offset(client: httpx.Client, archive: Archive, member: Member) -> int:
    """Where a member's bytes begin, past its own local header.

    The header's name and extra fields can be longer than the index's copy, so
    the length is read from the header itself rather than assumed.
    """
    header = _range(
        client, archive.url, member.header_offset, member.header_offset + 29
    )
    name_len, extra_len = struct.unpack("<HH", header[26:30])
    return member.header_offset + 30 + name_len + extra_len


def fetch(
    role: str,
    dest: Path | str = DEFAULT_DEST,
    *,
    sample: str = SAMPLE,
    chunk_bytes: int = 8 << 20,
    on_progress=None,
) -> Path:
    """Write one member of the archive to ``dest`` and return its path.

    A file already on disk at the member's declared size is kept, so a
    re-run of a notebook costs nothing. The member's stored checksum is
    verified as the bytes arrive: a truncated or corrupted download is
    refused rather than handed to a reader as data.
    """
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        archive = index(client)
        member = archive.matching(role_pattern(role, sample))
        target = dest / member.basename

        if target.exists() and target.stat().st_size == member.size:
            if on_progress:
                on_progress(member, member.compressed_size, member.compressed_size)
            return target

        if member.method not in (_STORED, _DEFLATED):
            raise ArchiveIndexError(
                f"{member.name} is stored with compression method "
                f"{member.method}, which this module cannot inflate."
            )

        start = _member_data_offset(client, archive, member)
        end = start + member.compressed_size - 1
        inflate = zlib.decompressobj(-15) if member.method == _DEFLATED else None
        digest = 0
        received = 0
        partial = target.with_name(target.name + ".part")

        try:
            with client.stream(
                "GET", archive.url, headers={"Range": f"bytes={start}-{end}"}
            ) as response:
                if response.status_code != 206:
                    raise ArchiveIndexError(
                        f"the host answered {response.status_code} to a range "
                        "request for the member's bytes"
                    )
                with open(partial, "wb") as handle:
                    for block in response.iter_bytes(chunk_bytes):
                        received += len(block)
                        out = inflate.decompress(block) if inflate else block
                        if out:
                            digest = zlib.crc32(out, digest)
                            handle.write(out)
                        if on_progress:
                            on_progress(member, received, member.compressed_size)
                    if inflate:
                        rest = inflate.flush()
                        if rest:
                            digest = zlib.crc32(rest, digest)
                            handle.write(rest)
        except BaseException:
            # Whatever went wrong, the bytes on disk are a fragment. Left
            # behind they are a file with the right name beside a file that
            # does not exist, and the next run cannot tell them apart.
            partial.unlink(missing_ok=True)
            raise

        if digest != member.crc:
            partial.unlink(missing_ok=True)
            raise ArchiveIndexError(
                f"{member.name} did not arrive intact: the checksum of what "
                "was received does not match the one the archive records."
            )
        partial.replace(target)
        return target


def human(nbytes: float) -> str:
    """A byte count a reader can judge at a glance."""
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(nbytes) < 1024 or unit == "GiB":
            return f"{nbytes:,.1f} {unit}" if unit != "B" else f"{nbytes:,.0f} B"
        nbytes /= 1024
    return f"{nbytes:,.1f} GiB"


def progress(member: Member, done: int, total: int) -> None:
    """A one-line progress report, for ``fetch(..., on_progress=progress)``."""
    share = done / total if total else 1.0
    sys.stderr.write(
        f"\r{member.basename}: {human(done)} of {human(total)} ({share:6.1%})"
    )
    if done >= total:
        sys.stderr.write("\n")
    sys.stderr.flush()


def _listing(archive: Archive) -> Iterator[str]:
    yield f"{archive.filename} — {human(archive.size)}, {len(archive.members)} members"
    for member in archive.members:
        if member.size:
            yield f"  {human(member.compressed_size):>12} on the wire  {member.name}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "roles",
        nargs="*",
        metavar="ROLE",
        help=f"which members to fetch: {', '.join(sorted(ROLES))}",
    )
    parser.add_argument("--sample", default=SAMPLE, help=f"section (default {SAMPLE})")
    parser.add_argument("--dest", default=str(DEFAULT_DEST), help="where to write")
    parser.add_argument(
        "--list", action="store_true", help="print the archive's index and stop"
    )
    args = parser.parse_args(argv)

    if args.list or not args.roles:
        for line in _listing(index()):
            print(line)
        return 0

    for role in args.roles:
        # Checked before the first byte: a typo in the last of three roles
        # should not be discovered after the first two have been fetched.
        role_pattern(role, args.sample)
    for role in args.roles:
        path = fetch(role, args.dest, sample=args.sample, on_progress=progress)
        print(f"{role}: {path.name} ({human(path.stat().st_size)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
