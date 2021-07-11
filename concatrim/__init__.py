import os.path
import os

import ffmpeg
import bisect
from typing import Tuple, Optional, List


class MultiFileConcatrimmer(object):
    def __init__(self, padding=0):
        self.files = {}
        self.pad_len = padding

    def add_file(self, filename):
        self.files[filename] = Concatrimmer(filename, self.pad_len)

    def concatrim_all(self, out_dir: str, prefix: str = None, suffix: str = None, dryrun=False) -> None:
        for filename, concatrimmer in self.files.items():
            concatrimmer.concatrim(out_dir, prefix, suffix, dryrun)


class Concatrimmer(object):
    _span_ori_starts: List[int] = []
    _span_ori_ends: List[int] = []
    _span_trm_starts: List[int] = []
    _span_trm_ends: List[int] = []
    pad_len: int
    sourcefile: str

    def __init__(self, source_filename: str, padding=0):
        """
        Initialize a Concatrimmer object with configuration given as arguments.
        
        :param padding: milliseconds to insert between trimmed pieces when joining them back.
        """
        source_filename = os.path.expanduser(source_filename)
        self.sourcefile = source_filename
        self.pad_len = padding
        self._empty_spans()
        self._empty_timing_map()
        self.ffmpeg_cmd = os.environ.get('FFMPEG_CMD', None)
        
    @property
    def pad_len(self):
        return self._pad_len
    
    @pad_len.setter
    def pad_len(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError('length of padding must be a positive integer in milliseconds.')
        self._pad_len = value
        self._empty_timing_map()
        
    def add_spans(self, *spans: Tuple[int, int]) -> None:
        """
        Pass a span in (start, end) format. Both time points must be in milliseconds.
        """
        for span in spans:
            for existing_span in self.spans():
                if self.is_overlapping(span, existing_span):
                    raise ValueError(f"Found an overlapping span: trying to add \"{list(span)}\", "
                                     f"but it overlaps with \"{list([existing_span])}\".")
            bisect.insort(self._span_ori_starts, span[0])
            bisect.insort(self._span_ori_ends, span[1])

    def _empty_spans(self):
        self._span_ori_starts = []
        self._span_ori_ends = []
    
    def _empty_timing_map(self):
        self._span_trm_starts = []
        self._span_trm_ends = []

    def spans(self):
        return zip(self._span_ori_starts, self._span_ori_ends)

    def concatrim(self, out_dir: str, prefix: str = None, suffix: str = None, dryrun=False) -> str:
        """
        Performs trim-then-concatenate using ffmpeg. 
        The new file will be named exactly identical to the original, 
        unless ``prefix`` and/or ``suffix`` are set. 
        
        :param out_dir: directory name to place output file
        :param prefix: prefix to attach in front of the new file name 
        :param suffix: suffix to attach at the end of the new file name (before the extension)
        :param dryrun: only prints the ffmpeg cmd to run (for debugging)
        :return: the name of the trimmed file
        """
        return self._concatrim_audio(out_dir, prefix, suffix, dryrun)

    def _concatrim_audio(self, out_dir: str, prefix: str = None, suffix: str = None, dryrun=False) -> str:
        """
        Method to actually run ffmpeg to generate a new media file in the out_dir. 
        The new file will be named exactly identical to the original, 
        unless ``prefix`` and/or ``suffix`` are set. 
        
        :param out_dir: directory name to place output file
        :param prefix: prefix to attach in front of the new file name 
        :param suffix: suffix to attach at the end of the new file name (before the extension)
        :return: the name of the trimmed audio file
        """
        if not os.path.exists(self.sourcefile):
            raise FileNotFoundError(f"source file {self.sourcefile} does not exist!")
        ori_basename = os.path.basename(self.sourcefile)
        ori_name, ori_ext = os.path.splitext(ori_basename)
        out_basename = f"{prefix if prefix is not None else ''}{ori_name}{suffix if suffix is not None else ''}{ori_ext}"
        out_fname = os.path.join(out_dir, out_basename)

        original = ffmpeg.input(self.sourcefile);
        trimmed = []
        pads = ffmpeg.input('anullsrc', f='lavfi').filter_multi_output('asplit')
        if len(self._span_ori_starts) == 0:
            raise ValueError("no spans configured to trim the input!")
        for i, (start, end) in enumerate(self.spans()):
            pad = pads[i].filter('atrim', duration=self.pad_len / 1000)  # self.pad_len is in milliseconds
            trimmed.append(original.filter('atrim', start=start / 1000, end=end / 1000))
            trimmed.append(pad)
        trimmed.pop(-1)  # fence posting
        ffmpeg_cmd = ffmpeg.concat(*trimmed, v=0, a=1)
        ffmpeg_cmd = ffmpeg_cmd.output(out_fname)
        # for debugging
        if dryrun:
            print(' '.join(ffmpeg_cmd.compile()))
        else:
            if os.path.exists(out_dir) and not os.path.isdir(out_dir):
                raise FileExistsError(f"cannot create a output directory, as a file already exist: {out_dir}")
            else:
                os.makedirs(out_dir, exist_ok=True)
                if self.ffmpeg_cmd is not None:
                    ffmpeg_cmd.run(overwrite_output=True, cmd=self.ffmpeg_cmd)
                else:
                    ffmpeg_cmd.run(overwrite_output=True)
        return out_fname

    @classmethod
    def is_overlapping(cls, span1, spane2):
        s1, e1 = span1
        s2, e2 = spane2
        return s1 <= e2 and s2 <= e1

    def _trimmed_timings(self) -> None:
        self._span_trm_starts = []
        self._span_trm_ends = []
        for i, (ori_start, ori_end) in enumerate(self.spans()):
            if i == 0:
                trimmed_start = 0
            else:
                trimmed_start = self.pad_len + self._span_trm_ends[-1]
            self._span_trm_starts.append(trimmed_start)
            self._span_trm_ends.append(ori_end - ori_start + trimmed_start)
        
    def _convert(self, query_timepoint, from_original_to_trimmed: bool = True) -> Optional[int]:
        
        # when no trimming is done, just return input
        if len(list(self.spans())) == 0:
            return query_timepoint

        # make sure spans are properly mapped
        if len(self._span_trm_starts) == 0 or len(self._span_trm_ends) == 0:
            self._trimmed_timings()
            
        # set direction
        if from_original_to_trimmed:
            origin_starts, target_starts = (self._span_ori_starts, self._span_trm_starts) 
            origin_ends, target_ends = (self._span_ori_ends, self._span_trm_ends)
        else:
            origin_starts, target_starts = (self._span_trm_starts, self._span_ori_starts)
            origin_ends, target_ends = (self._span_trm_ends, self._span_ori_ends)

        # figure out in which n-th target span the time point is 
        span_num = bisect.bisect(origin_starts, query_timepoint) - 1
        # next, check the point is valid and actually in the span
        if span_num < 0 or query_timepoint > origin_ends[span_num]:
            return None

        return target_starts[span_num] + (query_timepoint - origin_starts[span_num])

    def conv_to_trimmed(self, timepoint_from_original: int) -> Optional[int]:
        """
        Converts a time point from the original media to corresponding point in the trimmed media.
        Return None if the time point in query does not belong to any span for trimming.
        
        :param timepoint_from_original: a time point in the original media (milliseconds)
        :return: a time points in the trimmed media (milliseconds)
        """
        return self._convert(timepoint_from_original, True)
        
    def conv_to_original(self, timepoint_from_trimmed: int) -> Optional[int]:
        """
        Converts a time point from the trimmed media to corresponding point in the original media.
        Return None if the time point in query does not belong to any span in the trimmed. 
        
        :param timepoint_from_trimmed: a time point in the trimmed media (milliseconds)
        :return: a time points in the original media (milliseconds)
        """
        return self._convert(timepoint_from_trimmed, False)
