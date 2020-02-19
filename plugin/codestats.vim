"
" Vim side file to integrate support for codestats.net
"

" check for python 3.  Right now that is what is supported
if !has('python3')
	echomsg 'Python3 support required for vim-codestats'
	finish
endif

let g:vim_codestats_url = 'https://codestats.net/'
let g:vim_codestats_key = ''

" get the module path there the python file is located
let s:module_path = fnamemodify(resolve(expand('<sfile>:p')), ':h')

" load up the python file
execute 'py3file ' . s:module_path . '/codestats_request.py'

let b:current_xp = 0

" function to send xp - done on buffer write
function! s:send_xp()
	execute 'python3 codestats.add_xp("' . &filetype . '", ' . b:current_xp ')'
	let b:current_xp = 0
endfunction

" local function to add xp
function! s:add_xp()
	let b:current_xp += 1
endfunction

" local function to exit (which will send any remaining xp)
function! s:exit()
	execute 'python3 codestats.exit()'
endfunction

" autocommands to keep track of code stats
augroup codestats
    autocmd!
	autocmd InsertCharPre * call s:add_xp()
    autocmd TextChanged * call s:add_xp()
    autocmd VimLeavePre * call s:exit()
	autocmd BufWrite * call s:send_xp()
augroup END

function! CodeStatsXP()
	return 'CS: ' . b:current_xp
endfunction

