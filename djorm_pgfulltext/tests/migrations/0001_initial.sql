-- Create a new text search configuration to search in person names
-- This needs no stemming or thesaurus, only unaccent and lowercasing.

create extension if not exists unaccent;

create text search configuration public.names (parser='default');
alter text search configuration names alter mapping for asciiword, asciihword, hword_asciipart, hword_numpart, word, hword, numword, hword_part with unaccent, simple;
comment on text search configuration names is 'for text search in person names';

