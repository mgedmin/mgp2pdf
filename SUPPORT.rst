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

Partially supported:
- %prefix (doesn't actually do anything due to a bug)
- %deffont (only one directive accepted, if multiple are present they'll be mishandled)
- %area (xoffset/yoffset not allowed)

Ignored:
- %ccolor (ignored)
- %pcache (ignored)
- %system (pointless for PDFs anyway)
- %noop

Unsupported:

- .mgprc
- \\ escaping
- \\ line continuation
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
- %tab
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
