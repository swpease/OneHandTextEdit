# Table of Contents
- [Demo](#demo)
- [Rationale](#rationale)
- [How It Works](#how-it-works)
- [Suggested Additional Software and Settings](#suggested-additional-software-and-settings)
- [Use Basics](#use-basics)
- [Features](#features)
- [Maps](#maps)

&nbsp;

# Demo

[YouTube demo](https://www.youtube.com/watch?v=6XQs7i8cP24)

&nbsp;

# Rationale
There aren't a lot of good options for trying to input text to your computer without using two hands. Dictation works pretty well as of 2020, but it isn't perfect, which means you have to go back through and edit it. There are a few pieces of custom hardware out there, but they are rare, expensive, and the one that I managed to acquire was slow and difficult to learn, and stressed out my hand.

OneHandTextEdit addresses these problems by making use of something that all computer users already have (a keyboard), in a way that is highly familiar. You'll be surprised at how intuitive it is to do the mental change-over and start typing at an acceptable pace.

&nbsp;

# How It Works
Basically, the keyboard is mirrored along its middle. "P" and "Q", "F" and "J", "Z" and ".", and so on, with "B" all by its lonesome.

Making a dictionary that returns options for, say, "say" [(l or s), (a or ;), (t or y)] tends to yield only a single word. Of the 5000 most common words in contemporary American English, 94% are unique in such a dictionary. This means that when you want to use such heavy-hitters as "the" and "and", they just work.

&nbsp;

# Suggested Additional Software and Settings
Probably the biggest issue with trying to type with one hand is the non-letter keys. Stretching over to reach the escape, then the delete, then caps lock, is awful. On macOS, there is [Karabiner-Elements](https://karabiner-elements.pqrs.org/), which lets you switch around which keys do what. For instance, if you're typing with your right hand, you might map you tab key to the "\\" key.

Remapping keyboard layouts can be done with [Ukelele](https://software.sil.org/ukelele/), so you could, if you were crazy, set "a" to be "a", (shift + a) to be "O", (caps lock + a) to be "|", and so on. You could remap things however you want, but keep in mind the mirroring (e.g. that "art" and ";uy" both give you "art"). You might find it useful for getting some symbols over to a more convenient location.

I've become a fan of remapping some of the lesser used keys, such as ">" and "|", to be hidden under caps lock. So, I have my return key on my ";" spot, my ";" as (shift + comma), ":" as (shift + period) and my "<" and ">" tucked away under caps lock somewhere, at least for two-handed typing. Using it with my right hand, I am considering remapping "b" or "t" to "[", because it is less of a stretch.

I suggest you turn on sticky keys (available on macOS via Accessibility) to cut down on your stretching.

You might consider using dictation, usable on macOS with a double press of the command key, as well as an option in the Edit menu of OneHandTextEdit. Then, you could speak what you want to have written, and go back and correct any mistakes you catch, more easily with this program than otherwise.

&nbsp;

# Use Basics
Just type... pretend that your single hand is both hands. So, whether you go for the "d" or "k" key, your brain just says "middle finger middle row".

The words are coerced after you press space, return, or "/", so it will look like a jumbled mess until you hit one of those buttons.

There are two modes: "Insert" and "Wordcheck". Insert mode is like any old text editor, except you have the letter mirroring that is the core of this software. Wordcheck mode is for making changes to the default word selections, and completely changes what your letter keys do (see [below](#wordcheck-mode)).

For cases where there are multiple options, the dictionary returns the most commonly used (according to lexicographers) word first. Taking the word "say", the other options are "sat", "lay", and "lat". If you need to change a word, you can change into the "wordcheck" mode [Ctrl+I or Ctrl+E], navigate to your word of interest, and cycle through your other options. "Wordcheck" mode has its own set of controls, described below in a table.

If you like one of the other words more, you can change the default word by pressing "o" or "w".

&nbsp;

# Features
## Find and Replace
The find and replace feature **does not** provide any sort of text manipulation: what you type in is exactly what it finds / replaces.

## Auto-capitalization
Words at the start of paragraphs or sentences are automatically capitalized. Additionally, capitalized variants are provided for each non-capitalized word when in wordcheck mode.

## Add / Delete Word
You can edit the dictionary by either adding or deleting words from it. The words you add or delete are **case sensitive**. "bob" and "Bob" are two different options in the dictionary.

## Markdown
[Markdown](https://en.wikipedia.org/wiki/Markdown), specifically GitHub-flavored Markdown, is basically supported. *However*, HTML-style syntaxes ([supported tags](https://doc.qt.io/qt-5/richtext-html-subset.html)) are not explicitly supported (read: I have not explicitly checked for unhelpful coersions). You can view what your document looks like in Markdown with View --> Markdown Viewer. Note that it does not update while open. If you're unfamiliar with Markdown, I suggest the [Markdown cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet). This document was made in Markdown, using OneHandTextEdit.

## Rich Text
OneHandTextEdit currently provides only plaintext and Markdown support. "Rich text" refers to things like underlining, bolding, font size and color, images, spacing, and so on. Think MS Word.

&nbsp;

# Maps
## Insert Mode
| Left | Right |
|------|-------|
| q    | p     |
| w    | o     |
| e    | i     |
| r    | u     |
| t    | y     |
| a    | ;     |
| s    | l     |
| d    | k     |
| f    | j     |
| g    | h     |
| z    | .     |
| x    | ,     |
| c    | m     |
| v    | n     |
| b    | b     |

&nbsp;

## Wordcheck Mode
| Left         | Right        | Function                                 |
|--------------|--------------|------------------------------------------|
| w            | o            | Set word under cursor as default.        |
| e            | i            | Cycle backwards in alternate words list. |
| r            | u            | Cycle forwards in alternate words list.  |
|              |              |                                          |
| d            | k            | Move up one line.                        |
| f            | j            | Move down one Live.                      |
| s            | h            | Move left one word.                      |
| g            | l            | Move right one word.                     |
| c            | n            | Move left one character.                 |
| v            | m            | Move right one character.                |
|              |              |                                          |
| a            | ;            | The character ;              |
| z            | .            | The character .              |
| x            | ,            | The character ,              |
| A            | :            | The character :              |
| Z            | >            | The character >              |
| X            | <            | The character <              |
|              |              |                                          |
| [delete key] | [delete key] | Functions normally.                      |


&nbsp;
## Shortcuts (either mode)
| Left                | Right               | Function                         |
|---------------------|---------------------|----------------------------------|
| Command + E         | Command + I         | Toggle mode (Insert / Wordcheck) |
| Command + G         | Command + J         | Add word to dictionary           |
| Command + D         | Command + U         | Delete word from dictionary      |
|                     |                     |                                  |
| Command + N         | Command + B         | New                              |
| Command + T         | Command + O         | Open                             |
| Command + S         | Command + L         | Save                             |
| Command + Shift + S | Command + Shift + L | Save As                          |
| Command + R         | Command + P         | Print                            |
| Command + Shift + R | Command + Shift + P | Print Markdown                   |
| Command + Q         | Command + [         | Close app                        |
| Command + W         | Command + ]         | Close document                   |
|                     |                     |                                  |
| Command + Z         | Command + /         | Undo                             |
| Command + Shift + Z | Command + Y         | Redo                             |
| Command + X         | Command + .         | Cut                              |
| Command + C         | Command + ,         | Copy                             |
| Command + V         | Command + M         | Paste                            |
| Command + A         | Command + ;         | Select All                       |
| Command + F         | Command + Shift + J | Find and Replace                 |
|                     |                     |                                  |
| Command + =         | Command + =         | Zoom In                          |
| Command + -         | Command + -         | Zoom Out                         |
| Command + Shift + C | Command + Shift + M | Markdown Viewer                  |
