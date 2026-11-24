-- lurpa.lua — filtre du socle Quarto LURPA.
--
-- Diapositives (revealjs) : ajoute à chaque titre de diapositive (niveau 2) la
-- signature ENS Paris-Saclay et, juste après, le logo LURPA. Les deux éléments
-- sont écrits une fois, pendant la construction du document par Pandoc : aucun
-- script ne s'exécute au redimensionnement, Reveal.js ne peut pas les dupliquer.
--   lurpa-logo: assets/logo-lurpa.png   chemin depuis la racine du projet (défaut)
--   lurpa-logo: false                   aucun logo
--
-- PDF (LaTeX) : rend les classes du socle, qui sans cela n'existent qu'en CSS.
--   ::: {.key-result} … :::  (ou .highlight-box)  → environnement lurpakeyresult
--   [texte]{.course-label}                        → \lurpacourselabel{texte}

local logo_path = "assets/logo-lurpa.png"
local logo_enabled = true

local SIGNATURE =
  '<span class="ens-signature" aria-hidden="true"><i></i><i></i><i></i><i></i></span>'

-- Chemin donné depuis la racine du projet → chemin depuis le document.
local function from_project_root(path)
  if path:match("^%a[%w+.-]*:") or path:sub(1, 1) == "/" then
    return path
  end
  local offset = quarto.project and quarto.project.offset
  if offset == nil or offset == "" or offset == "." then
    return path
  end
  return offset .. "/" .. path
end

local function read_meta(meta)
  local value = meta["lurpa-logo"]
  if value == nil then
    return nil
  end
  if type(value) == "boolean" then
    logo_enabled = value
  else
    local s = pandoc.utils.stringify(value)
    if s == "" or s == "false" then
      logo_enabled = false
    else
      logo_path = s
    end
  end
  return nil
end

local function slide_header(header)
  if header.level ~= 2 or not quarto.doc.is_format("revealjs") then
    return nil
  end
  table.insert(header.content, 1, pandoc.RawInline("html", SIGNATURE))
  if not logo_enabled then
    return header
  end
  local img = string.format(
    '<img class="lurpa-logo" src="%s" alt="LURPA">', from_project_root(logo_path))
  return { header, pandoc.RawBlock("html", img) }
end

local KEY_RESULT_CLASSES = { "key-result", "highlight-box" }

local function latex_div(div)
  if not quarto.doc.is_format("latex") then
    return nil
  end
  for _, class in ipairs(KEY_RESULT_CLASSES) do
    if div.classes:includes(class) then
      local blocks = pandoc.List({ pandoc.RawBlock("latex", "\\begin{lurpakeyresult}") })
      blocks:extend(div.content)
      blocks:insert(pandoc.RawBlock("latex", "\\end{lurpakeyresult}"))
      return blocks
    end
  end
  return nil
end

local function latex_span(span)
  if not quarto.doc.is_format("latex") or not span.classes:includes("course-label") then
    return nil
  end
  local inlines = pandoc.List({ pandoc.RawInline("latex", "\\lurpacourselabel{") })
  inlines:extend(span.content)
  inlines:insert(pandoc.RawInline("latex", "}"))
  return inlines
end

-- Les métadonnées sont lues d'abord (deux passes successives).
return {
  { Meta = read_meta },
  { Header = slide_header, Div = latex_div, Span = latex_span },
}
