"""
Copyright 2017 Rahul Gupta, Soham Pal, Aditya Kanade, Shirish Shevade.
Indian Institute of Science.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import tempfile
import time
import sys
import subprocess32 as subprocess
import numpy as np


class FailedToGetLineNumberException(Exception):
    pass


class InvalidFixLocationException(Exception):
    pass


class SubstitutionFailedException(Exception):
    pass


def compilation_errors(string):
    name1 = int(time.time() * 10**6)
    name2 = np.random.random_integers(0, 1000)
    filename = 'temp/tempfile_%d_%d.c' % (name1, name2)
    out_file = 'temp/temp.out'

    with open(filename, 'w+') as f:
        f.write(string)

    shell_string = "gcc -w -std=c99 -pedantic %s -lm -o %s" % (filename, out_file)

    try:
        result = subprocess.check_output(
            shell_string, timeout=30, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        result = e.output

    os.unlink('%s' % (filename,))
    error_set = []

    for line in result.splitlines():
        if 'error:' in line:
            error_set.append(line)

    return error_set, result


# Input: tokenized program
# Returns: array of lines, each line is tokenized
def get_lines(program_string):
    lines = []
    ignore_tokens = [str(n) for n in range(10)]
    for token in program_string.split():
        if token == '~':
            if len(lines) > 0:
                lines[-1] = lines[-1].rstrip(' ')
            lines.append('')
        elif token not in ignore_tokens:
            lines[-1] += token + ' '
    return lines


# Input: output of get_lines() (tokenized lines)
# Result: Tokenized program
def recompose_program(lines):
    recomposed_program = ''

    for i, line in enumerate(lines):
        for digit in str(i):
            recomposed_program += digit + ' '

        recomposed_program += '~ '
        recomposed_program += line + ' '

    # Should return recomposed_program.rstrip()???
    return recomposed_program


# Fetches a specific line from the program
def fetch_line(program_string, line_number, include_line_number=True):
    result = ''

    if include_line_number:
        for digit in str(line_number):
            result += digit + ' '

        result += '~ '

    result += get_lines(program_string)[line_number]
    # assert result.strip() != ''
    return result

# Input: tokenized program
# Returns: source code, optionally clang-formatted


def tokens_to_source(tokens, name_dict, clang_format=False, name_seq=None):
    result = ''
    type_ = None

    reverse_name_dict = {}
    name_count = 0

    for k, v in name_dict.iteritems():
        reverse_name_dict[v] = k

    for token in tokens.split():
        try:
            prev_type_was_op = (type_ == 'op')

            type_, content = token.split('>_')
            type_ = type_.lstrip('_<')

            if type_ == 'id':
                if name_seq is not None:
                    content = name_seq[name_count]
                    name_count += 1
                else:
                    try:
                        content = reverse_name_dict[content.rstrip('@')]
                    except KeyError:
                        content = 'new_id_' + content.rstrip('@')
            elif type_ == 'number':
                content = content.rstrip('#')

            if type_ == 'directive' or type_ == 'include' or type_ == 'op' or type_ == 'type' or type_ == 'keyword' or type_ == 'APIcall':
                if type_ == 'op' and prev_type_was_op:
                    result = result[:-1] + content + ' '
                else:
                    result += content + ' '
            elif type_ == 'id':
                result += content + ' '
            elif type_ == 'number':
                result += '0 '
            elif type_ == 'string':
                result += '"String" '
            elif type_ == 'char':
                result += "'c' "
        except ValueError:
            if token == '~':
                result += '\n'

    if not clang_format:
        return result

    source_file = tempfile.NamedTemporaryFile(suffix=".c", delete=False)
    source_file.write(result)
    source_file.close()

    shell_string = 'clang-format %s' % source_file.name
    clang_output = subprocess.check_output(
        shell_string, timeout=30, shell=True)
    os.unlink(source_file.name)

    return clang_output


# This function returns the line where we indexed into the string
# [program_string] is a tokenized program
# [char_index] is an index into program_string
def isolate_line(program_string, char_index):
    begin = program_string[:char_index].rfind('~') - 2

    while begin - 2 > 0 and program_string[begin - 2] in [str(i) for i in range(10)]:
        begin -= 2

    if program_string[char_index:].find('~') == -1:
        end = len(program_string)
    else:
        end = char_index + program_string[char_index:].find('~') - 2

        while end - 2 > 0 and program_string[end - 2] in [str(i) for i in range(10)]:
            end -= 2

        end -= 1

    return program_string[begin:end]


def extract_line_number(line):
    line_split = line.split('~')
    if len(line_split) > 0:
        num_list = line_split[0].strip().split()
        if len(num_list) >= 0:
            try:
                num = int(''.join(num_list))
            except ValueError:
                raise FailedToGetLineNumberException(line)
            else:
                return num
    raise FailedToGetLineNumberException(line)


# Checks if all of the ids in the fix are present in the original program
# fix_string is the token string of the fix
# program_string is the token string of the program
def fix_ids_are_in_program(program_string, fix_string):
    prog_ids = []
    fix_ids = []

    for token in program_string.split():
        if '_<id>_' in token and token not in prog_ids:
            prog_ids.append(token)

    for token in fix_string.split():
        if '_<id>_' in token and token not in fix_ids:
            fix_ids.append(token)

    for fix_id in fix_ids:
        if fix_id not in prog_ids:
            return False

    return True


def replace_ids(new_line, old_line):
    ids = []

    for token in old_line.split():
        if '_<id>_' in token:
            ids.append(token)

    result = ''
    counter = 0

    for token in new_line.split():
        if '_<id>_' not in token:
            result += token + ' '
        else:
            result += ids[counter] + ' '
            counter += 1

    return result.strip()


def _remove_line_number(fix):
    return fix.split('~')[1]


def _truncate_fix(fix):
    result = ''

    for token in fix.split():
        if token == '_eos_':
            break
        else:
            result += token + ' '

    return result.strip()


def apply_fix(program, fix, kind='replace', flag_replace_ids=True):
    # Break up program string into lines
    lines = get_lines(program)

    # Truncate the fix
    fix = _truncate_fix(fix)

    # Make sure there are two parts
    if len(fix.split('~')) != 2:
        # print 'cant partition in 2 on ~'
        raise InvalidFixLocationException

    # Retrieve insertion location
    try:
        if kind == 'replace':
            fix_location = extract_line_number(fix)
        else:
            assert kind == 'insert'

            if fix.split()[0] != '_<insertion>_':
                # print "Warning: First token did not suggest insertion (should not happen)"
                pass

            fix_location = extract_line_number(' '.join(fix.split()[1]))
    except FailedToGetLineNumberException:
        # print 'FailedToGetLineNumberException'
        raise InvalidFixLocationException

    # Remove line number
    fix = _remove_line_number(fix)

    # Insert the fix
    if kind == 'replace':
        try:
            if lines[fix_location].count('_<id>_') != fix.count('_<id>_'):
                raise SubstitutionFailedException

            if flag_replace_ids:
                lines[fix_location] = replace_ids(fix, lines[fix_location])
            else:
                lines[fix_location] = fix

        except IndexError:
            # print 'IndexError!!  fix location:', fix_location, 'len lines:', len(lines)
            raise InvalidFixLocationException
    else:
        assert kind == 'insert'
        lines.insert(fix_location + 1, fix)

    return recompose_program(lines)


def make_dir_if_not_exists(path):
    try:
        os.makedirs(path)
    except:
        pass


def get_curr_time_string():
    return time.strftime("%b %d %Y %H:%M:%S")


class logger():
    def _open(self):
        if not self.open:
            try:
                self.handle = open(self.log_file, 'a+')
                self.open = True
            except Exception as e:
                print os.getcwd()
                raise e
        else:
            raise RuntimeError(
                'ERROR: Trying to open already opened log-file!')

    def close(self):
        if self.open:
            self.handle.close()
            self.open = False
        else:
            raise RuntimeError(
                'ERROR: Trying to close already closed log-file!')

    def __init__(self, log_file, move_to_logs_dir=True):
        self.log_file = log_file + '.txt' if '.txt' not in log_file else log_file
        if move_to_logs_dir and not self.log_file.startswith('logs/'):
            self.log_file = os.path.join('logs', log_file)
        self.open = False
        self.handle = None
        self._open()

        self.terminal = sys.stdout

        self.log('\n\n-----------------------| Started logging at: {} |----------------------- \n'.format(get_curr_time_string()))

    # for backward compatibility
    def log(self, *msg_list):

        msg_list = map(str, msg_list)
        msg = ' '.join(msg_list)

        if not self.open:
            self._open()

        self.handle.write(msg + '\n')
        self.handle.flush()

        print msg
        self.terminal.flush()

    # set ** sys.stdout = logger(filename) ** and then simply use print call
    def write(self, message):
        if not self.open:
            self._open()

        self.handle.write(message)
        self.terminal.write(message)

    @property
    def terminal(self):
        return self.terminal

    def flush(self):
        self.terminal.flush()
        self.handle.flush()


def get_rev_dict(dict_):
    assert len(dict_) > 0, 'passed dict has size zero'
    rev_dict_ = {}
    for key, value in dict_.iteritems():
        rev_dict_[value] = key

    return rev_dict_


def vstack_with_right_padding(arraylist):
    assert arraylist is not None and len(
        arraylist) > 0, 'arraylist:\n{}'.format(arraylist)

    col_max = max([np.shape(each)[1] for each in arraylist])
    row_total = sum([np.shape(each)[0] for each in arraylist])

    new_arraylist = []

    for each in arraylist:
        assert len(np.shape(each)) == 2, 'np.shape(): {}'.format(
            np.shape(each))
        i, j = np.shape(each)
        if j < col_max:
            pad_slice = np.zeros((i, col_max - j), np.int)
            new_arraylist.append(np.hstack((each, pad_slice)))
        elif j == col_max:
            new_arraylist.append(each)
        else:
            print 'shapes: {}'.format([np.shape(each) for each in arraylist])
            print 'col_max: {}'.format(col_max)
            raise RuntimeError('col_max computed wrong!')

    output = np.vstack(new_arraylist)
    assert (row_total, col_max) == np.shape(output)
    return output


def make_equal_size_matrices(y, y_hat):
    '''Both args should be 2d matrices of shape [batch_size X seq_len].'''

    batch_size_y, seq_len_y = np.shape(y)
    batch_size_y_hat, seq_len_y_hat = np.shape(y_hat)

    assert batch_size_y == batch_size_y_hat, 'batch size mismatch, {}, {}'.format(
        batch_size_y, batch_size_y_hat)

    if seq_len_y < seq_len_y_hat:
        y_hat = y_hat[:, :seq_len_y]

    elif seq_len_y_hat < seq_len_y:
        pad_slice = np.zeros(
            (batch_size_y_hat, seq_len_y - seq_len_y_hat), y_hat.dtype)
        y_hat = np.concatenate((y_hat, pad_slice), axis=1)

    return y, y_hat, batch_size_y


def get_accuracy(Y, Y_hat, which):
    Y, Y_hat, batch_size = make_equal_size_matrices(Y, Y_hat)

    if which == 'sequence':
        accuracy = 0.0
        for y, y_hat in zip(Y, Y_hat):
            if np.array_equal(y, y_hat):
                accuracy += 1.0
        return accuracy / float(batch_size)

    elif which == 'token':
        return np.sum(np.equal(Y, Y_hat)) / float(np.prod(np.shape(Y)))

    else:
        raise ValueError(
            'get_accuracy(): which should be one of *sequence*, and *token*')


class Accuracy_calculator_for_deepfix():
    '''Input format of a fix is: [loc ~ fix_tokens] for typo network, e.g.:    1 4 ~ int id_a op_, id_b
    and [_<insertion>_ loc ~ fix_tokens] for id network, e.g.:       _<insertion>_ 8 ~ _<type>_int _<id>_1@ _<op>_[ _<number>_# _<op>_] _<op>_;'''

    def __init__(self, tilde_token):
        self.tilde_token = tilde_token

    def get_error_location(self, in_):
        out_ = []

        for token in in_:
            if token != self.tilde_token:
                out_.append(token)
            else:
                assert out_ is not None, 'tilde_token:{} \ninput: {}'.format(
                    self.tilde_token, in_)
                return out_

    def get_df_fix(self, in_):
        out_ = []
        tilde_count = 0

        for token in in_:
            if token != self.tilde_token and tilde_count >= 1:
                out_.append(token)
            elif token == self.tilde_token:
                tilde_count += 1

        return out_

    def get_all_accuracies(self, y, y_hat):
        localization_equality = np.array_equal(
            self.get_error_location(y), self.get_error_location(y_hat))
        fix_equality = localization_equality and np.array_equal(
            self.get_df_fix(y), self.get_df_fix(y_hat))

        return localization_equality, fix_equality
