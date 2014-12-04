Feature support matrix
----------------------

See /usr/share/doc/mgp/SYNTAX.gz on Debian/Ubuntu systems for a list of
MagicPoint directives (or should I call them "commands")?

Supported:

- # comment lines
- %% comment lines
- %size
- %fore
- %left
- %center
- %right
- %cont
- %nodefault
- %newimage
- %default
- %page
- %vgap
- %mark
- %again
- %filter/%endfilter
- %font
- %include

Partially supported:

- \\ escaping (\\xHH is not supported)
- %prefix (doesn't actually do anything due to a bug)
- %deffont (only one directive accepted, if multiple are present they'll be mishandled)
- %area (xoffset/yoffset not allowed)
- %tab (parsing is done, but it has no effet)

Ignored:

- %ccolor (pointless for PDFs)
- %pcache (pointless for PDFs)
- %system (pointless for PDFs)
- %noop (it's supposed to do nothing)

Unsupported:

- .mgprc
- \\ line continuation
- %tab <id> and &id
- %back
- %bgrad
- %leftfill
- %rightfill
- %shrink (not supported by mgp itself also)
- %lcutin (can't animate PDFs anyway)
- %rcutin (can't animate PDFs anyway)
- %xfont
- %vfont
- %tfont
- %tmfont
- %tfont0
- %psfont
- %bar
- %valign
- %image
- %icon
- %bimage
- %hgap
- %pause
- %vfcap
- %tfdir
- %embed "filename"/%endembed
- %anim (can't really support it for PDFs)
- %charset (we assume UTF-8 instead, which is not supported by mgp itself)
- %opaque
- %setsup
- %sup
- %sub

Unsupported directives produce warnings in verbose mode and are ignored.
