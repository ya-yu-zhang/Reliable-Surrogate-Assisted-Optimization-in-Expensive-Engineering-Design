-- Keep a subsection's short introduction and its first display together.
function Blocks(blocks)
  local result = {}
  local i = 1
  while i <= #blocks do
    local a, b, c = blocks[i], blocks[i+1], blocks[i+2]
    if a and b and c and a.t == 'Header' and b.t == 'Para' and c.t == 'Para'
       and #c.content == 1 and c.content[1].t == 'Math'
       and c.content[1].mathtype == 'DisplayMath' then
      result[#result+1] = pandoc.RawBlock('latex', '\\begin{samepage}')
      result[#result+1] = a
      result[#result+1] = b
      result[#result+1] = c
      result[#result+1] = pandoc.RawBlock('latex', '\\end{samepage}')
      i = i + 3
    elseif a and a.t == 'Table' then
      -- Every result table is shorter than a page; preserve all rows together.
      result[#result+1] = pandoc.RawBlock('latex', '\\par\\noindent\\begin{minipage}{\\linewidth}')
      result[#result+1] = a
      result[#result+1] = pandoc.RawBlock('latex', '\\end{minipage}\\par')
      i = i + 1
    else
      result[#result+1] = a
      i = i + 1
    end
  end
  return result
end
