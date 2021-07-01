class TFAgent:
    """ Class for loading and using a policy """

    def __init__(
        self,
        policy_path: Path,
    ):
        """
        Args:
            policy_path: path to the training results, i.e. the folder that
                         contains the params.pkl and params.json file.
        """
        # Initialize ray
        ray.init(local_mode=True, ignore_reinit_error=True)

        self._load_from_policy_path(policy_path)

        if self.policy.is_recurrent():
            self.policy_state = self.policy.get_initial_state()

        self.env_proxy = self.trainer.env_creator(
            self.config["env_config"], env_class=RoboFishProxyEnv
        )
        self.env_proxy.reset()

        self.action = np.zeros((1, 2))
        self.prev_reward = None

        self.first_step = True

    def _load_from_policy_file(self, policy_file):
        weights = {}
        with h5py.File(policy_file, "r") as f:
            for policy in f.keys():
                for layer in f[policy].keys():
                    for key in f[policy][layer].keys():
                        weights[f"{policy}/{layer}/{key}"] = np.array(
                            f[policy][layer][key]
                        )
            self.config_str = f.attrs["config"]
            self.config = json.loads(self.config_str)
        if (
            self.config["callbacks"]
            == "<class 'ray.rllib.agents.callbacks.DefaultCallbacks'>"
        ):
            # `callbacks` must be a callable method that
            # returns a subclass of DefaultCallbacks
            self.config["callbacks"] = lambda: DefaultCallbacks
        self.trainer = PPOTrainer(config=self.config)
        self.trainer.get_policy().set_weights(weights)
        self.policy = self.trainer.get_policy()

    def _load_from_policy_path(self, policy_path):
        with open(Path(policy_path) / "params.pkl", "rb") as f:
            self.config = pickle.load(f)
        with open(Path(policy_path) / "params.json", "rb") as f:
            self.config_str = f.read()
        self.config["num_workers"] = 0
        self.config["num_envs_per_worker"] = 0
        print(self.config)
        self.trainer = PPOTrainer(config=self.config)
        checkpoint_path, self.checkpoint = get_checkpoint(policy_path)
        if checkpoint_path.exists():
            print("Restoring from checkpoint path", checkpoint_path)
            self.trainer.restore(str(checkpoint_path))
        else:
            raise FileNotFoundError(
                f"Could not restore trainer from checkpoint {checkpoint_path}"
            )
        self.policy = self.trainer.get_policy()

    def set_world(self, w, h):
        self.world_bounds = np.vstack(
            [
                position_to_gym(np.array([0, h], dtype=np.float), w, h),
                position_to_gym(np.array([w, 0], dtype=np.float), w, h),
            ]
        )
        self.goal = np.array([0.4, 0.4])

    def tick(self, robot_pose, fish_coordinates, step_logger=None):
        self.first_step = False
        state = get_state(robot_pose=robot_pose, fish_coordinates=fish_coordinates)
        self.env_proxy.inject_state(
            state=state, goal=self.goal, step_logger=step_logger
        )
        observation, self.prev_reward, _, _ = self.env_proxy.step(action=self.action)
        self.action = self.trainer.compute_action(observation=observation).flatten()
        return self.action

    def update_goal(self, robot_pose, fish_coordinates):
        if fish_coordinates.size:
            self.goal, goal_reached = get_goal(
                goal=self.goal, coordinates=fish_coordinates
            )
        else:
            # for policy without fish
            self.goal, goal_reached = get_goal(
                goal=self.goal, coordinates=robot_pose[:2].reshape((1, 2))
            )
        return goal_reached


def get_goal(
    goal: np.ndarray,
    coordinates: np.ndarray,
    tolerance: float = 0.05,
):
    """
    Keep current goal until coordinates get close enough.
    Return the goal in the opposite corner if goal was reached.
    For policies with fish, use fish_coordinates.
    For policies without fish, use robot_coordinates.
    """
    if np.sqrt(np.sum((goal - coordinates) ** 2, axis=1)) <= tolerance:
        if (goal == 0.4).all():
            return np.array([-0.4, -0.4]), True
        else:
            return np.array([0.4, 0.4]), True
    else:
        return goal, False


def get_state(robot_pose, fish_coordinates):
    """
    Get state in the required shape:
    pos_x, pos_y, angle for each body.
    For fish the angle is set to zero.
    """
    robot = np.concatenate(
        (robot_pose[:2], [np.arctan2(robot_pose[3], robot_pose[2])])
    ).reshape((1, 3))

    if fish_coordinates.size:
        return np.concatenate(
            (
                robot,
                np.concatenate(
                    (fish_coordinates, np.zeros((fish_coordinates.shape[0], 1))), axis=1
                ),
            )
        )
    else:
        return robot