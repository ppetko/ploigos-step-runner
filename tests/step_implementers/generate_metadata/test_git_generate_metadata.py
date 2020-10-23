import os
from io import IOBase, StringIO

from testfixtures import TempDirectory
from tests.helpers.base_step_implementer_test_case import \
    BaseStepImplementerTestCase

from git import Repo 
from git import InvalidGitRepositoryError

import mock
from unittest.mock import MagicMock, patch

from tssc.config.config import Config
from tssc.step_result import StepResult
from tssc.workflow_result import WorkflowResult
from tssc.step_implementers.generate_metadata import Git

from test_utils import *

# TODO once the git _run_step method is rewritten we need to rewrite these tests properly with mock

class TestStepImplementerGitGenerateMetadata(BaseStepImplementerTestCase):
    def create_step_implementer(
            self,
            step_config={},
            test_config={},
            results_dir_path='',
            results_file_name='',
            work_dir_path=''
    ):
        return self.create_given_step_implementer(
            step_implementer=Git,
            step_config=step_config,
            test_config=test_config,
            results_dir_path=results_dir_path,
            results_file_name=results_file_name,
            work_dir_path=work_dir_path
        )

    def test_step_implementer_config_defaults(self):
        defaults = Git.step_implementer_config_defaults()
        expected_defaults = {
            'repo-root': './',
            'build-string-length': 7
        }
        self.assertEqual(defaults, expected_defaults)

    def test_required_runtime_step_config_keys(self):
        required_keys = Git.required_runtime_step_config_keys()
        expected_required_keys = ['repo-root','build-string-length']
        self.assertEqual(required_keys, expected_required_keys)

    def test_run_step_pass(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)

            step_config = {
                'repo-root': str(temp_dir.path)
            }
            test_config = {'step-name': 'generate-metadata', 'implementer': 'Git'}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
            )
            
            result = step_implementer._run_step()

            #cheating because we don't want to fully mock this yet
            self.assertTrue(result.success, True)

    def test_root_dir_is_not_git_repo(self):
        with TempDirectory() as temp_dir:
            step_config = {
                'repo-root': '/'
            }
            test_config = {'step-name': 'generate-metadata', 'implementer': 'Git'}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = f'Given directory (repo_root) is not a Git repository'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_root_dir_is_bare_git_repo(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path), bare=True)

            step_config = {
                'repo-root': str(temp_dir.path)
            }
            test_config = {'step-name': 'generate-metadata', 'implementer': 'Git'}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = f'Given directory (repo_root) is a bare Git repository'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_no_commit_history(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            step_config = {
                'repo-root': str(temp_dir.path)
            }
            test_config = {'step-name': 'generate-metadata', 'implementer': 'Git'}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = f'Given directory (repo_root) is a git branch (git_branch) with no commit history'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())

    def test_git_repo_with_single_commit_on_master(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)

            step_config = {
                'repo-root': str(temp_dir.path)
            }
            test_config = {'step-name': 'generate-metadata', 'implementer': 'Git'}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
            )
            
            result = step_implementer._run_step()

            #cheating because we don't want to fully mock this yet
            self.assertTrue(result.success, True)

    def test_git_repo_with_single_commit_on_feature(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            create_git_commit_with_sample_file(temp_dir, repo)

            # checkout a feature branch
            git_new_branch = repo.create_head('feature/test0')
            git_new_branch.checkout()

            step_config = {
                'repo-root': str(temp_dir.path)
            }
            test_config = {'step-name': 'generate-metadata', 'implementer': 'Git'}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
            )
            
            result = step_implementer._run_step()

            #cheating because we don't want to fully mock this yet
            self.assertEqual(result.get_artifact_value('pre-release'), 'feature_test0')
            self.assertTrue(result.success, True)

    def test_directory_is_detached(self):
        with TempDirectory() as temp_dir:
            repo = Repo.init(str(temp_dir.path))

            # create commits
            create_git_commit_with_sample_file(temp_dir, repo, 'test0')
            create_git_commit_with_sample_file(temp_dir, repo, 'test1')
            
            # detach head
            repo.git.checkout('master^')

            step_config = {
                'repo-root': str(temp_dir.path)
            }
            test_config = {'step-name': 'generate-metadata', 'implementer': 'Git'}

            step_implementer = self.create_step_implementer(
                step_config=step_config,
                test_config=test_config,
            )
            
            result = step_implementer._run_step()

            expected_step_result = StepResult(step_name='generate-metadata', sub_step_name='Git', sub_step_implementer_name='Git')
            expected_step_result.success = False
            expected_step_result.message = f'Expected a Git branch in given directory (repo_root) but has a detached head'

            self.assertEqual(result.get_step_result(), expected_step_result.get_step_result())