#!/usr/bin/python

# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Unit tests for cros_mark_as_stable.py."""

import mox
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                '..', '..'))
from chromite.buildbot import constants
from chromite.buildbot import constants
from chromite.lib import cros_build_lib
from chromite.scripts import cros_mark_as_stable


# pylint: disable=W0212,R0904
class NonClassTests(mox.MoxTestBase):
  def setUp(self):
    mox.MoxTestBase.setUp(self)
    self.mox.StubOutWithMock(cros_build_lib, 'RunCommand')
    self.mox.StubOutWithMock(cros_build_lib, 'RunCommandCaptureOutput')
    self._branch = 'test_branch'
    self._target_manifest_branch = 'cros/master'

  def testPushChange(self):
    git_log = 'Marking test_one as stable\nMarking test_two as stable\n'
    fake_description = 'Marking set of ebuilds as stable\n\n%s' % git_log
    self.mox.StubOutWithMock(cros_mark_as_stable, '_DoWeHaveLocalCommits')
    self.mox.StubOutWithMock(cros_mark_as_stable.GitBranch, 'CreateBranch')
    self.mox.StubOutWithMock(cros_mark_as_stable.GitBranch, 'Exists')
    self.mox.StubOutWithMock(cros_build_lib, 'GitPushWithRetry')
    self.mox.StubOutWithMock(cros_build_lib, 'GetTrackingBranch')
    self.mox.StubOutWithMock(cros_build_lib, 'SyncPushBranch')
    self.mox.StubOutWithMock(cros_build_lib, 'CreatePushBranch')
    self.mox.StubOutWithMock(cros_build_lib, 'RunGitCommand')

    cros_mark_as_stable._DoWeHaveLocalCommits(
        self._branch, self._target_manifest_branch, '.').AndReturn(True)
    cros_build_lib.GetTrackingBranch('.', for_push=True).AndReturn(
        ['gerrit', 'refs/remotes/gerrit/master'])
    cros_build_lib.SyncPushBranch('.', 'gerrit', 'refs/remotes/gerrit/master')
    cros_mark_as_stable._DoWeHaveLocalCommits(
        self._branch, 'refs/remotes/gerrit/master', '.').AndReturn(True)
    result = cros_build_lib.CommandResult(output=git_log)
    cros_build_lib.RunCommandCaptureOutput(
        ['git', 'log', '--format=format:%s%n%n%b',
         'refs/remotes/gerrit/master..%s' % self._branch],
        cwd='.').AndReturn(result)
    cros_build_lib.CreatePushBranch('merge_branch', '.')
    cros_build_lib.RunGitCommand('.', ['merge', '--squash', self._branch])
    cros_build_lib.RunGitCommand('.', ['commit', '-m', fake_description])
    cros_build_lib.RunGitCommand('.', ['config', 'push.default', 'tracking'])
    cros_build_lib.GitPushWithRetry('merge_branch', '.', dryrun=False)
    self.mox.ReplayAll()
    cros_mark_as_stable.PushChange(self._branch, self._target_manifest_branch,
                                   False, '.')
    self.mox.VerifyAll()


class GitBranchTest(mox.MoxTestBase):

  def setUp(self):
    mox.MoxTestBase.setUp(self)
    # Always stub RunCommmand out as we use it in every method.
    self.mox.StubOutWithMock(cros_build_lib, 'RunCommand')
    self.mox.StubOutWithMock(cros_build_lib, 'RunCommandCaptureOutput')
    self._branch = self.mox.CreateMock(cros_mark_as_stable.GitBranch)
    self._branch_name = 'test_branch'
    self._branch.branch_name = self._branch_name
    self._target_manifest_branch = 'cros/test'
    self._branch.tracking_branch = self._target_manifest_branch
    self._branch.cwd = '.'

  def testCheckoutCreate(self):
    # Test init with no previous branch existing.
    self._branch.Exists(self._branch_name).AndReturn(False)
    cros_build_lib.RunCommandCaptureOutput(['repo', 'start', self._branch_name,
                                            '.'], print_cmd=False, cwd='.')
    self.mox.ReplayAll()
    cros_mark_as_stable.GitBranch.Checkout(self._branch)
    self.mox.VerifyAll()

  def testCheckoutNoCreate(self):
    # Test init with previous branch existing.
    self._branch.Exists(self._branch_name).AndReturn(True)
    cros_build_lib.RunCommandCaptureOutput(['git', 'checkout', '-f',
                                            self._branch_name], print_cmd=False,
                                           cwd='.')
    self.mox.ReplayAll()
    cros_mark_as_stable.GitBranch.Checkout(self._branch)
    self.mox.VerifyAll()

  def testExists(self):
    branch = cros_mark_as_stable.GitBranch(self._branch_name,
                                           self._target_manifest_branch, '.')
    # Test if branch exists that is created
    result = cros_build_lib.CommandResult(output=self._branch_name + '\n')
    cros_build_lib.RunCommandCaptureOutput(['git', 'branch'], print_cmd=False,
                                           cwd='.').AndReturn(result)
    self.mox.ReplayAll()
    self.assertTrue(branch.Exists())
    self.mox.VerifyAll()


if __name__ == '__main__':
  unittest.main()