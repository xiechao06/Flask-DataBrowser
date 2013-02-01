let SessionLoad = 1
if &cp | set nocp | endif
let s:cpo_save=&cpo
set cpo&vim
inoremap <silent> <S-Tab> =BackwardsSnippet()
inoremap <Plug>ZenCodingAnchorizeSummary :call zencoding#anchorizeURL(1)a
inoremap <Plug>ZenCodingAnchorizeURL :call zencoding#anchorizeURL(0)a
inoremap <Plug>ZenCodingRemoveTag :call zencoding#removeTag()a
inoremap <Plug>ZenCodingSplitJoinTagInsert :call zencoding#splitJoinTag()a
inoremap <Plug>ZenCodingToggleComment :call zencoding#toggleComment()a
inoremap <Plug>ZenCodingImageSize :call zencoding#imageSize()a
inoremap <Plug>ZenCodingPrev :call zencoding#moveNextPrev(1)
inoremap <Plug>ZenCodingNext :call zencoding#moveNextPrev(0)
inoremap <Plug>ZenCodingBalanceTagOutwardInsert :call zencoding#balanceTag(-1)a
inoremap <Plug>ZenCodingBalanceTagInwardInsert :call zencoding#balanceTag(1)a
inoremap <Plug>ZenCodingExpandWord u:call zencoding#expandAbbr(1)a
inoremap <Plug>ZenCodingExpandAbbr u:call zencoding#expandAbbr(0)a
imap <silent> <Plug>IMAP_JumpBack =IMAP_Jumpfunc('b', 0)
imap <silent> <Plug>IMAP_JumpForward =IMAP_Jumpfunc('', 0)
inoremap <silent> <Plug>NERDCommenterInInsert  <BS>:call NERDComment(0, "insert")
map <silent>  <Plug>(RivHelpFile)
map <silent> hf <Plug>(RivHelpFile)
map <silent>  <Plug>(RivHelpTodo)
map <silent> ht <Plug>(RivHelpTodo)
map <silent>  <Plug>(RivScratchView)
map <silent> sv <Plug>(RivScratchView)
map <silent>  <Plug>(RivScratchCreate)
map <silent> sc <Plug>(RivScratchCreate)
map <silent> 	 <Plug>(RivProjectHtmlIndex)
map <silent> wi <Plug>(RivProjectHtmlIndex)
map <silent>  <Plug>(RivProjectList)
map <silent> wa <Plug>(RivProjectList)
map <silent>  <Plug>(RivProjectIndex)
map <silent> ww <Plug>(RivProjectIndex)
snoremap <silent> 	 i<Right>=TriggerSnippet()
vmap <NL> <Plug>IMAP_JumpForward
nmap <NL> <Plug>IMAP_JumpForward
snoremap  b<BS>
nmap A <Plug>ZenCodingAnchorizeSummary
nmap a <Plug>ZenCodingAnchorizeURL
nmap k <Plug>ZenCodingRemoveTag
nmap j <Plug>ZenCodingSplitJoinTagNormal
nmap / <Plug>ZenCodingToggleComment
nmap i <Plug>ZenCodingImageSize
nmap N <Plug>ZenCodingPrev
nmap n <Plug>ZenCodingNext
vmap D <Plug>ZenCodingBalanceTagOutwardVisual
nmap D <Plug>ZenCodingBalanceTagOutwardNormal
vmap d <Plug>ZenCodingBalanceTagInwardVisual
nmap d <Plug>ZenCodingBalanceTagInwardNormal
nmap ; <Plug>ZenCodingExpandWord
nmap , <Plug>ZenCodingExpandNormal
vmap , <Plug>ZenCodingExpandVisual
snoremap % b<BS>%
snoremap ' b<BS>'
nmap ,ca <Plug>NERDCommenterAltDelims
vmap ,cA <Plug>NERDCommenterAppend
nmap ,cA <Plug>NERDCommenterAppend
vmap ,c$ <Plug>NERDCommenterToEOL
nmap ,c$ <Plug>NERDCommenterToEOL
vmap ,cu <Plug>NERDCommenterUncomment
nmap ,cu <Plug>NERDCommenterUncomment
vmap ,cn <Plug>NERDCommenterNest
nmap ,cn <Plug>NERDCommenterNest
vmap ,cb <Plug>NERDCommenterAlignBoth
nmap ,cb <Plug>NERDCommenterAlignBoth
vmap ,cl <Plug>NERDCommenterAlignLeft
nmap ,cl <Plug>NERDCommenterAlignLeft
vmap ,cy <Plug>NERDCommenterYank
nmap ,cy <Plug>NERDCommenterYank
vmap ,ci <Plug>NERDCommenterInvert
nmap ,ci <Plug>NERDCommenterInvert
vmap ,cs <Plug>NERDCommenterSexy
nmap ,cs <Plug>NERDCommenterSexy
vmap ,cm <Plug>NERDCommenterMinimal
nmap ,cm <Plug>NERDCommenterMinimal
vmap ,c  <Plug>NERDCommenterToggle
nmap ,c  <Plug>NERDCommenterToggle
vmap ,cc <Plug>NERDCommenterComment
nmap ,cc <Plug>NERDCommenterComment
map ,s :source ~/.vim/session/Session.vim
map ,p :e ~/.temp
map ,m :e ~/.memo
map ,q :e ~/.question
map ,d :e ~/.digest
map ,t :e ~/.todo
map ,e :e ~/.vimrc
snoremap U b<BS>U
vmap [% [%m'gv``
snoremap \ b<BS>\
vmap ]% ]%m'gv``
snoremap ^ b<BS>^
snoremap ` b<BS>`
vmap a% [%v]%
nmap gx <Plug>NetrwBrowseX
snoremap <Left> bi
snoremap <Right> a
snoremap <BS> b<BS>
snoremap <silent> <S-Tab> i<Right>=BackwardsSnippet()
nnoremap <silent> <Plug>NetrwBrowseX :call netrw#NetrwBrowseX(expand("<cWORD>"),0)
nnoremap <Plug>ZenCodingAnchorizeSummary :call zencoding#anchorizeURL(1)
nnoremap <Plug>ZenCodingAnchorizeURL :call zencoding#anchorizeURL(0)
nnoremap <Plug>ZenCodingRemoveTag :call zencoding#removeTag()
nnoremap <Plug>ZenCodingSplitJoinTagNormal :call zencoding#splitJoinTag()
nnoremap <Plug>ZenCodingToggleComment :call zencoding#toggleComment()
nnoremap <Plug>ZenCodingImageSize :call zencoding#imageSize()
nnoremap <Plug>ZenCodingPrev :call zencoding#moveNextPrev(1)
nnoremap <Plug>ZenCodingNext :call zencoding#moveNextPrev(0)
vnoremap <Plug>ZenCodingBalanceTagOutwardVisual :call zencoding#balanceTag(-2)
nnoremap <Plug>ZenCodingBalanceTagOutwardNormal :call zencoding#balanceTag(-1)
vnoremap <Plug>ZenCodingBalanceTagInwardVisual :call zencoding#balanceTag(2)
nnoremap <Plug>ZenCodingBalanceTagInwardNormal :call zencoding#balanceTag(1)
nnoremap <Plug>ZenCodingExpandWord :call zencoding#expandAbbr(1)
nnoremap <Plug>ZenCodingExpandNormal :call zencoding#expandAbbr(3)
vnoremap <Plug>ZenCodingExpandVisual :call zencoding#expandAbbr(2)
vmap <silent> <Plug>IMAP_JumpBack `<i=IMAP_Jumpfunc('b', 0)
vmap <silent> <Plug>IMAP_JumpForward i=IMAP_Jumpfunc('', 0)
vmap <silent> <Plug>IMAP_DeleteAndJumpBack "_<Del>i=IMAP_Jumpfunc('b', 0)
vmap <silent> <Plug>IMAP_DeleteAndJumpForward "_<Del>i=IMAP_Jumpfunc('', 0)
nmap <silent> <Plug>IMAP_JumpBack i=IMAP_Jumpfunc('b', 0)
nmap <silent> <Plug>IMAP_JumpForward i=IMAP_Jumpfunc('', 0)
nmap <silent> <Plug>NERDCommenterAppend :call NERDComment(0, "append")
nnoremap <silent> <Plug>NERDCommenterToEOL :call NERDComment(0, "toEOL")
vnoremap <silent> <Plug>NERDCommenterUncomment :call NERDComment(1, "uncomment")
nnoremap <silent> <Plug>NERDCommenterUncomment :call NERDComment(0, "uncomment")
vnoremap <silent> <Plug>NERDCommenterNest :call NERDComment(1, "nested")
nnoremap <silent> <Plug>NERDCommenterNest :call NERDComment(0, "nested")
vnoremap <silent> <Plug>NERDCommenterAlignBoth :call NERDComment(1, "alignBoth")
nnoremap <silent> <Plug>NERDCommenterAlignBoth :call NERDComment(0, "alignBoth")
vnoremap <silent> <Plug>NERDCommenterAlignLeft :call NERDComment(1, "alignLeft")
nnoremap <silent> <Plug>NERDCommenterAlignLeft :call NERDComment(0, "alignLeft")
vmap <silent> <Plug>NERDCommenterYank :call NERDComment(1, "yank")
nmap <silent> <Plug>NERDCommenterYank :call NERDComment(0, "yank")
vnoremap <silent> <Plug>NERDCommenterInvert :call NERDComment(1, "invert")
nnoremap <silent> <Plug>NERDCommenterInvert :call NERDComment(0, "invert")
vnoremap <silent> <Plug>NERDCommenterSexy :call NERDComment(1, "sexy")
nnoremap <silent> <Plug>NERDCommenterSexy :call NERDComment(0, "sexy")
vnoremap <silent> <Plug>NERDCommenterMinimal :call NERDComment(1, "minimal")
nnoremap <silent> <Plug>NERDCommenterMinimal :call NERDComment(0, "minimal")
vnoremap <silent> <Plug>NERDCommenterToggle :call NERDComment(1, "toggle")
nnoremap <silent> <Plug>NERDCommenterToggle :call NERDComment(0, "toggle")
vnoremap <silent> <Plug>NERDCommenterComment :call NERDComment(1, "norm")
nnoremap <silent> <Plug>NERDCommenterComment :call NERDComment(0, "norm")
noremap <Plug>(RivGetLatest) :RivGetLatest
noremap <Plug>(RivSpecification) :RivSpecification
noremap <Plug>(RivCheatSheet) :RivCheatSheet
noremap <Plug>(RivPrimer) :RivPrimer
noremap <Plug>(RivQuickStart) :RivQuickStart
noremap <Plug>(RivInstruction) :RivInstruction
noremap <Plug>(RivIntro) :RivIntro
noremap <Plug>(RivVimTest) : RivVimTest
noremap <Plug>(RivHelpSection) :RivHelpSection
noremap <Plug>(RivHelpFile) :RivHelpFile
noremap <Plug>(RivHelpTodo) :RivHelpTodo
noremap <Plug>(RivSuperMEnter) :RivSuperMEnter
noremap <Plug>(RivSuperSEnter) :RivSuperSEnter
noremap <Plug>(RivSuperCEnter) :RivSuperCEnter
noremap <Plug>(RivSuperEnter) :RivSuperEnter
noremap <Plug>(RivTestObj) :RivTestObj
noremap <Plug>(RivTestTest) :RivTestTest
noremap <Plug>(RivTestFold1) :RivTestFold1
noremap <Plug>(RivTestFold0) :RivTestFold0
noremap <Plug>(RivTestReload) :RivTestReload
noremap <Plug>(Riv2BuildPath) :Riv2BuildPath
noremap <Plug>(Riv2Latex) :Riv2Latex
noremap <Plug>(Riv2Xml) :Riv2Xml
noremap <Plug>(Riv2S5) :Riv2S5
noremap <Plug>(Riv2Odt) :Riv2Odt
noremap <Plug>(Riv2HtmlProject) :Riv2HtmlProject
noremap <Plug>(Riv2HtmlAndBrowse) :Riv2HtmlAndBrowse
noremap <Plug>(Riv2HtmlFile) :Riv2HtmlFile
noremap <Plug>(RivDeleteFile) :RivDeleteFile
noremap <Plug>(RivCreateExplicitMark) :RivCreateExplicitMark
noremap <Plug>(RivCreateTransition) :RivCreateTransition
noremap <Plug>(RivCreateHyperLink) :RivCreateHyperLink
noremap <Plug>(RivCreateLiteralBlock) :RivCreateLiteralBlock
noremap <Plug>(RivCreateLiteralInline) : RivCreateLiteralInline
noremap <Plug>(RivCreateInterpreted) : RivCreateInterpreted
noremap <Plug>(RivCreateStrong) : RivCreateStrong
noremap <Plug>(RivCreateEmphasis) : RivCreateEmphasis
noremap <Plug>(RivCreateContent) :RivCreateContent
noremap <Plug>(RivCreateTime) :RivCreateTime
noremap <Plug>(RivCreateDate) :RivCreateDate
noremap <Plug>(RivCreateFoot) :RivCreateFoot
noremap <Plug>(RivCreateLink) :RivCreateLink
noremap <Plug>(RivTodoUpdateCache) :RivTodoUpdateCache
noremap <Plug>(RivTodoType4) :RivTodoType4
noremap <Plug>(RivTodoType3) :RivTodoType3
noremap <Plug>(RivTodoType2) :RivTodoType2
noremap <Plug>(RivTodoType1) :RivTodoType1
noremap <Plug>(RivTodoAsk) :RivTodoAsk
noremap <Plug>(RivTodoPrior) :RivTodoPrior
noremap <Plug>(RivTodoDate) :RivTodoDate
noremap <Plug>(RivTodoDel) :RivTodoDel
noremap <Plug>(RivTodoToggle) :RivTodoToggle
noremap <Plug>(RivListType4) :RivListType4
noremap <Plug>(RivListType3) :RivListType3
noremap <Plug>(RivListType2) :RivListType2
noremap <Plug>(RivListType1) :RivListType1
noremap <Plug>(RivListType0) :RivListType0
noremap <Plug>(RivListDelete) :RivListDelete
noremap <Plug>(RivListToggle) :RivListToggle
noremap <Plug>(RivListSup) :RivListSup
noremap <Plug>(RivListSub) :RivListSub
noremap <Plug>(RivListNew) :RivListNew
noremap <Plug>(RivTablePrevCell) :RivTablePrevCell
noremap <Plug>(RivTableNextCell) :RivTableNextCell
noremap <Plug>(RivTableFormat) :RivTableFormat
noremap <Plug>(RivTableCreate) :RivTableCreate
noremap <Plug>(RivTitle0) :RivTitle0
noremap <Plug>(RivTitle6) :RivTitle6
noremap <Plug>(RivTitle5) :RivTitle5
noremap <Plug>(RivTitle4) :RivTitle4
noremap <Plug>(RivTitle3) :RivTitle3
noremap <Plug>(RivTitle2) :RivTitle2
noremap <Plug>(RivTitle1) :RivTitle1
noremap <Plug>(RivItemToggle) :RivItemToggle
noremap <Plug>(RivItemClick) :RivItemClick
noremap <Plug>(RivNormEqual) :RivNormEqual
noremap <Plug>(RivNormLeft) :RivNormLeft
noremap <Plug>(RivNormRight) :RivNormRight
noremap <Plug>(RivShiftEqual) :RivShiftEqual
noremap <Plug>(RivShiftLeft) :RivShiftLeft
noremap <Plug>(RivShiftRight) :RivShiftRight
noremap <Plug>(RivLinkPrev) :RivLinkPrev
noremap <Plug>(RivLinkNext) :RivLinkNext
noremap <Plug>(RivLinkOpen) :RivLinkOpen
noremap <Plug>(RivFoldUpdate) :RivFoldUpdate
noremap <Plug>(RivFoldAll) :RivFoldAll
noremap <Plug>(RivFoldToggle) :RivFoldToggle
noremap <Plug>(RivScratchView) :RivScratchView
noremap <Plug>(RivScratchCreate) :RivScratchCreate
noremap <Plug>(RivProjectHtmlIndex) :RivProjectHtmlIndex
noremap <Plug>(RivProjectList) :RivProjectList
noremap <Plug>(RivProjectIndex) :RivProjectIndex
inoremap <silent> o =VST_Ornaments()
inoremap <silent> 	 =TriggerSnippet()
imap <NL> <Plug>IMAP_JumpForward
imap  
inoremap <silent> 	 =ShowAvailableSnips()
imap A <Plug>ZenCodingAnchorizeSummary
imap a <Plug>ZenCodingAnchorizeURL
imap k <Plug>ZenCodingRemoveTag
imap j <Plug>ZenCodingSplitJoinTagInsert
imap / <Plug>ZenCodingToggleComment
imap i <Plug>ZenCodingImageSize
imap N <Plug>ZenCodingPrev
imap n <Plug>ZenCodingNext
imap D <Plug>ZenCodingBalanceTagOutwardInsert
imap d <Plug>ZenCodingBalanceTagInwardInsert
imap ; <Plug>ZenCodingExpandWord
imap , <Plug>ZenCodingExpandAbbr
let &cpo=s:cpo_save
unlet s:cpo_save
set autoindent
set background=dark
set backspace=indent,eol,start
set completeopt=menu
set expandtab
set fileencodings=ucs-bom,utf-8,default,latin1
set formatoptions=tcqmM
set guifont=Courier\ 10\ Pitch\ 14
set guioptions=aegiLt
set helplang=cn
set hlsearch
set printoptions=paper:a4
set ruler
set runtimepath=~/.vim/bundle/vundle,~/.vim/bundle/riv.vim,~/.vim/bundle/L9,~/.vim/bundle/FuzzyFinder,~/.vim,/var/lib/vim/addons,/usr/share/vim/vimfiles,/usr/share/vim/vim73,/usr/share/vim/vimfiles/after,/var/lib/vim/addons/after,~/.vim/after,~/.vim/bundle/vundle/,~/.vim/bundle/vundle/after,~/.vim/bundle/riv.vim/after,~/.vim/bundle/L9/after,~/.vim/bundle/FuzzyFinder/after
set shiftwidth=4
set suffixes=.bak,~,.swp,.o,.info,.aux,.log,.dvi,.bbl,.blg,.brf,.cb,.ind,.idx,.ilg,.inx,.out,.toc
set tabstop=4
set wildignore=*.pyc
let s:so_save = &so | let s:siso_save = &siso | set so=0 siso=0
let v:this_session=expand("<sfile>:p")
silent only
cd ~/work/lite-mms-dev/Flask-DataBrowser/flask_databrowser/example
if expand('%') == '' && !&modified && line('$') <= 1 && getline(1) == ''
  let s:wipebuf = bufnr('%')
endif
set shortmess=aoO
badd +24 make_test_data.py
badd +1 ~/.vim/templates/template.py
badd +9 basemain.py
badd +6 __main__.py
badd +13 models.py
badd +10 tox.ini
badd +0 ../../requirements.txt
badd +0 setup.py
args make_test_data.py
edit ../../requirements.txt
set splitbelow splitright
wincmd _ | wincmd |
split
1wincmd k
wincmd w
set nosplitbelow
set nosplitright
wincmd t
set winheight=1 winwidth=1
exe '1resize ' . ((&lines * 26 + 27) / 55)
exe '2resize ' . ((&lines * 26 + 27) / 55)
argglobal
setlocal keymap=
setlocal noarabic
setlocal autoindent
setlocal balloonexpr=
setlocal nobinary
setlocal bufhidden=
setlocal buflisted
setlocal buftype=
setlocal nocindent
setlocal cinkeys=0{,0},0),:,0#,!^F,o,O,e
setlocal cinoptions=
setlocal cinwords=if,else,while,do,for,switch
set colorcolumn=78
setlocal colorcolumn=78
setlocal comments=s1:/*,mb:*,ex:*/,://,b:#,:%,:XCOMM,n:>,fb:-
setlocal commentstring=/*%s*/
setlocal complete=.,w,b,u,t,i
setlocal concealcursor=
setlocal conceallevel=0
setlocal completefunc=
setlocal nocopyindent
setlocal cryptmethod=
setlocal nocursorbind
setlocal nocursorcolumn
setlocal nocursorline
setlocal define=
setlocal dictionary=
setlocal nodiff
setlocal equalprg=
setlocal errorformat=
setlocal expandtab
if &filetype != 'text'
setlocal filetype=text
endif
setlocal foldcolumn=0
setlocal foldenable
setlocal foldexpr=0
setlocal foldignore=#
setlocal foldlevel=0
setlocal foldmarker={{{,}}}
setlocal foldmethod=manual
setlocal foldminlines=1
setlocal foldnestmax=20
setlocal foldtext=foldtext()
setlocal formatexpr=
setlocal formatoptions=tcqmM
setlocal formatlistpat=^\\s*\\d\\+[\\]:.)}\\t\ ]\\s*
setlocal grepprg=
setlocal iminsert=2
setlocal imsearch=2
setlocal include=
setlocal includeexpr=
setlocal indentexpr=
setlocal indentkeys=0{,0},:,0#,!^F,o,O,e
setlocal noinfercase
setlocal iskeyword=@,48-57,_,192-255
setlocal keywordprg=
setlocal nolinebreak
setlocal nolisp
setlocal nolist
setlocal makeprg=
setlocal matchpairs=(:),{:},[:]
setlocal modeline
setlocal modifiable
setlocal nrformats=octal,hex
set number
setlocal number
setlocal numberwidth=4
setlocal omnifunc=
setlocal path=
setlocal nopreserveindent
setlocal nopreviewwindow
setlocal quoteescape=\\
setlocal noreadonly
setlocal norelativenumber
setlocal norightleft
setlocal rightleftcmd=search
setlocal noscrollbind
setlocal shiftwidth=4
setlocal noshortname
setlocal nosmartindent
setlocal softtabstop=0
setlocal nospell
setlocal spellcapcheck=[.?!]\\_[\\])'\"\	\ ]\\+
setlocal spellfile=
setlocal spelllang=en
setlocal statusline=
setlocal suffixesadd=
setlocal swapfile
setlocal synmaxcol=3000
if &syntax != 'text'
setlocal syntax=text
endif
setlocal tabstop=4
setlocal tags=
setlocal textwidth=0
setlocal thesaurus=
setlocal noundofile
setlocal nowinfixheight
setlocal nowinfixwidth
setlocal wrap
setlocal wrapmargin=0
silent! normal! zE
let s:l = 1 - ((0 * winheight(0) + 13) / 26)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
1
normal! 0
wincmd w
argglobal
edit setup.py
inoreabbr <buffer> cfrom =IMAP_PutTextWithMovement("from <++> import <++>")
inoreabbr <buffer> ctry =IMAP_PutTextWithMovement("try:\n<++>\nexcept <++>:\n    <++>")
inoreabbr <buffer> cifelse =IMAP_PutTextWithMovement("if <++>:\n<++>\nelse:\n<++>")
inoreabbr <buffer> cif =IMAP_PutTextWithMovement("if <++>:\n<++>")
inoreabbr <buffer> cfor =IMAP_PutTextWithMovement("for <++> in <++>:\n<++>")
inoreabbr <buffer> cclass =IMAP_PutTextWithMovement("class <++>:\n<++>")
inoreabbr <buffer> cfun =IMAP_PutTextWithMovement("def <++>(<++>):\n<++>\nreturn <++>")
setlocal keymap=
setlocal noarabic
setlocal autoindent
setlocal balloonexpr=
setlocal nobinary
setlocal bufhidden=
setlocal buflisted
setlocal buftype=
setlocal nocindent
setlocal cinkeys=0{,0},0),:,!^F,o,O,e
setlocal cinoptions=
setlocal cinwords=if,else,while,do,for,switch
set colorcolumn=78
setlocal colorcolumn=78
setlocal comments=s1:/*,mb:*,ex:*/,://,b:#,:XCOMM,n:>,fb:-
setlocal commentstring=#%s
setlocal complete=.,w,b,u,t,i
setlocal concealcursor=
setlocal conceallevel=0
setlocal completefunc=
setlocal nocopyindent
setlocal cryptmethod=
setlocal nocursorbind
setlocal nocursorcolumn
setlocal nocursorline
setlocal define=
setlocal dictionary=
setlocal nodiff
setlocal equalprg=
setlocal errorformat=%+P[%f],%t:\ %#%l:%m,%Z,%+IYour\ code%m,%Z,%-G%.%#
setlocal expandtab
if &filetype != 'python'
setlocal filetype=python
endif
setlocal foldcolumn=0
setlocal foldenable
setlocal foldexpr=GetPythonFold(v:lnum)
setlocal foldignore=#
setlocal foldlevel=0
setlocal foldmarker={{{,}}}
setlocal foldmethod=expr
setlocal foldminlines=1
setlocal foldnestmax=20
setlocal foldtext=PythonFoldText()
setlocal formatexpr=
setlocal formatoptions=tcqmM
setlocal formatlistpat=^\\s*\\d\\+[\\]:.)}\\t\ ]\\s*
setlocal grepprg=
setlocal iminsert=2
setlocal imsearch=2
setlocal include=^\\s*\\(from\\|import\\)
setlocal includeexpr=substitute(v:fname,'\\.','/','g')
setlocal indentexpr=GetPythonIndent(v:lnum)
setlocal indentkeys=!^F,o,O,<:>,0),0],0},=elif,=except
setlocal noinfercase
setlocal iskeyword=@,48-57,_,192-255
setlocal keywordprg=pydoc
setlocal nolinebreak
setlocal nolisp
setlocal nolist
setlocal makeprg=(echo\ '[%]';\ pylint\ -r\ y\ %)
setlocal matchpairs=(:),{:},[:]
setlocal modeline
setlocal modifiable
setlocal nrformats=octal,hex
set number
setlocal number
setlocal numberwidth=4
setlocal omnifunc=pythoncomplete#Complete
setlocal path=
setlocal nopreserveindent
setlocal nopreviewwindow
setlocal quoteescape=\\
setlocal noreadonly
setlocal norelativenumber
setlocal norightleft
setlocal rightleftcmd=search
setlocal noscrollbind
setlocal shiftwidth=4
setlocal noshortname
setlocal nosmartindent
setlocal softtabstop=0
setlocal nospell
setlocal spellcapcheck=[.?!]\\_[\\])'\"\	\ ]\\+
setlocal spellfile=
setlocal spelllang=en
setlocal statusline=
setlocal suffixesadd=.py
setlocal swapfile
setlocal synmaxcol=3000
if &syntax != 'python'
setlocal syntax=python
endif
setlocal tabstop=4
setlocal tags=
setlocal textwidth=0
setlocal thesaurus=
setlocal noundofile
setlocal nowinfixheight
setlocal nowinfixwidth
setlocal wrap
setlocal wrapmargin=0
let s:l = 8 - ((7 * winheight(0) + 13) / 26)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
8
normal! 011l
wincmd w
2wincmd w
exe '1resize ' . ((&lines * 26 + 27) / 55)
exe '2resize ' . ((&lines * 26 + 27) / 55)
tabnext 1
if exists('s:wipebuf')
  silent exe 'bwipe ' . s:wipebuf
endif
unlet! s:wipebuf
set winheight=1 winwidth=20 shortmess=filnxtToO
let s:sx = expand("<sfile>:p:r")."x.vim"
if file_readable(s:sx)
  exe "source " . fnameescape(s:sx)
endif
let &so = s:so_save | let &siso = s:siso_save
doautoall SessionLoadPost
unlet SessionLoad
" vim: set ft=vim :
